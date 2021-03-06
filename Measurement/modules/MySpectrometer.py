#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 23:53:59 2016

@author: nils
"""
import numpy as np
#import RPi.GPIO as gpio

class MySpectrometer(object):
     
    def __init__(self, sb, sbs, parent, device):
        
        try:
            self.access = sbs.Spectrometer(device)
        except sbs.SeaBreezeError:
            # test if this actually catches the error! 
            # Otherwise, revert to the "open_device" workaround.
            device.close()
            try:
                self.access = sbs.Spectrometer(device)
            except sbs.SeaBreezeError:
                print('Ocean optics device already open')
            
        self.WL = self.access.wavelengths() 
        self.parent = parent
        self.IT = self.parent.IT
        self.NonlinearityCorrection = False
        self.DarkCurrentCorrection = False
        self.stream = None
        
    
    def close(self):
        self.access.close()
        
    
    def start_stream(self, ViewPort, Plot):
        self.stream = self.parent.LiveFeed(self, ViewPort, Plot)
        self.stream.start()
    
    
    def light_on(self):
        self.access.lamp_set_enable(True)
    
    
    def light_off(self):
        self.access.lamp_set_enable(False)
       
    
    def set_IT(self, integration_time_milisec):
        integration_time = 1000*integration_time_milisec
        self.IT = integration_time
        self.access.integration_time_micros(self.IT)
    
    
    def get_signal(self):            
        signal = self.access.intensities(correct_dark_counts=self.DarkCurrentCorrection,
                                         correct_nonlinearity=self.NonlinearityCorrection)
        return signal
        
        
    def multiple_spectra(self, n):
        spectra=[]
        for i in range(n+1):
            spectra.append(self.get_signal())
        if n==1:
            return {'intensities':spectra[1:][-1], 'N':n, 'IT':self.IT, 'detector':self.name}
        else:
            return {'intensities':spectra[1:], 'N':n, 'IT':self.IT, 'detector':self.name}

        
    def get_spectrum(self):    
        spectrum = self.access.spectrum(correct_dark_counts=self.DarkCurrentCorrection,
                                        correct_nonlinearity=self.NonlinearityCorrection)
        return spectrum
    
    def get_dark(self):
        self.access.lamp_set_enable(False)        
        dark =  self.access.intensities(correct_dark_counts=self.DarkCurrentCorrection,
                                        correct_nonlinearity=self.NonlinearityCorrection)
        return dark
    

    def avg_spec(self, n):
        spectra=[]
        for i in range(n+1):
            spectra.append(self.get_signal())
        yerr = np.nanstd(spectra[1:], axis=0)
        mean = np.nanmean(spectra[1:], axis=0)
        return {'mean_spec':mean, 'std_dev':yerr, 'N':n, 'IT':self.IT}
    
    def avg_dark_corrected(self, n): 
        """
        interactive semi-automatic spectrum acquisition with dark correction
        """
        import time
        
        input('please turn the lightsource OFF ')
        time.sleep(self.parent.IT/1000)
        dark = self.avg_spec(n)
        
        input('Saved dark. Now, please turn the lightsource ON ')
        time.sleep(self.parent.IT/1000)
        i = self.avg_spec(n)
        
        i['dark'] = dark['mean spec']
        
        i_corrected = i['mean spec'] - dark['mean spec']
        i['mean spec'] = i_corrected
        
        return i
        print('Dark-corrected intensity acquired.')
