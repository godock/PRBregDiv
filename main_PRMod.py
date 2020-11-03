"""
Phase retrieval from modified spectrograms

Phase retrieval with Bregman divergences and application to audio signal recovery
Pierre-Hugo Vial, Paul Magron, Thomas Oberlin, Cédric Févotte

October 2020
"""

# %% Packages import 

import sys, getopt
import librosa as l
import numpy as np
import glob
import soundfile as sf

from functions import stft, istft, GLA, FGLA, GLADMM, GradDesc, ADMM, init_random, noiseDenoise_Wiener, savepath

def main(argv):
    database = 'speech'
    n_files = 10
    n_iter = 2500
    len_sec = 2
    gamma = 0.99
    rho = 1e-1
    snrs = [10, 0, -10, -20]
    
    #Parse command line arguments
    try:
        opts, args = getopt.getopt(argv, 'hd:n:f:s:', ['dataset=', 'niter=', 'snr='])
    except getopt.GetoptError:
        print('main_PRMod.py -d <dataset> -n <number of iterations> -f <number of files> -s <input SNR in dB>')
        sys.exit(2)
    for opt, arg in opts:
        if opt =='-h':
            print('main_PRMod.py -d <dataset> -n <number of iterations> -f <number of files> -s <input SNR in dB>')
            sys.exit()    
        elif opt in ['-d', '--dataset']:
            database = arg
        elif opt in ['-n', '--niter']:
            n_iter = int(arg)
        elif opt in ['-f']:
            n_files = int(arg)
        elif opt in ['-s']:
            snrs=[int(arg)]
    
    #Database import
    if database=='music':
        dataset_path = r'datasets/music'
        files = glob.glob(dataset_path + r'/*.mp3')
    elif database=='speech':
        dataset_path = r'datasets/speech'
        files = glob.glob(dataset_path + r'/*.wav')
    for i in range(len(files)):
        files[i]=files[i].replace('\\','/')
    files = files[:n_files]
    newpath=savepath(['PRMod', database])
    
    #Procedure
    #Gradient descent algorithms (loss, direction, step size, d)
    GD_algs = [('IS','right',1e-7,2),
               ('KL','right',1e-4,1),('KL','left',1e-1,1),
               ('b05','right',1e-1,1),('b05','left',1e-6,1),
               ('l2','left',1,1),
               ('b05','right',1e-3,2),('b05','left',1e-5,2),
               ('KL', 'right', 1e-1,2),('KL', 'left', 1e-1,2),
               ('l2','left',1e-5,2)]
    #ADMM algorithms (optimized cost, direction, d)
    ADMM_algs = [('IS','left',1), ('KL', 'left',1), ('l2', 'left',1)]
    
    #Execution
    c_file=0
    for file_path in files:
    	#Loading original signal and preprocessing
        xo, sr = l.load(file_path) 
        xo = xo[:int(len_sec*sr)]
        xo = istft(stft(xo))
        
        sf.write(newpath+'%i_ORIGINAL.wav'%c_file, xo, sr, subtype = 'PCM_24')
        for snrdB in snrs:
            print('File %i/%i, input SNR = %s dB'%(c_file+1, n_files, snrdB))
    		#Initialisation
            M = noiseDenoise_Wiener(xo, snrdB) #Producing modified magnitude spectrogram
            X_init = init_random(M) #Initialisation with random phase
            x_init = istft(X_init)
            sf.write(newpath+'%i_%s_INIT.wav'%(c_file, snrdB), x_init, sr, subtype = 'PCM_24')
            
    		#Processing gradient descent algorithms
            for alg in GD_algs:
                d=alg[3]
                print('Gradient descent: %s, %s, d=%i'%(alg[0], alg[1], d))
                R = np.power(M,d)
                x_gen = GradDesc(x_init, R, d, alg[0], alg[1], alg[2], it=n_iter, gamma=gamma)
                sf.write(newpath+'%i_%s_GD_%s_%s_d%i.wav'%(c_file, snrdB, alg[0], alg[1], alg[3]), x_gen, sr, subtype = 'PCM_24')
            
    		#Processing ADMM algorithms		
            for alg in ADMM_algs:
                d=alg[2]
                print('ADMM: %s, %s, d=%i'%(alg[0], alg[1], d))
                R = np.power(M,d)
                x_gen = ADMM(x_init, R, d, alg[0], alg[1], it=n_iter, rho=rho)
                sf.write(newpath+'%i_%s_ADMM_%s_%s_d%i.wav'%(c_file, snrdB, alg[0], alg[1], d), x_gen, sr, subtype = 'PCM_24')
            
    		#Processing GLA
            print('Griffin-Lim Algorithm') 
            X_gla = GLA(X_init, M, it=n_iter)
            x_gla = istft(X_gla)
            sf.write(newpath+'%i_%s_GLA.wav'%(c_file, snrdB), x_gla, sr, subtype = 'PCM_24')
            
    		#Processing FGLA
            print('Fast Griffin-Lim Algorithm')
            X_fgla = FGLA(X_init, M, it=n_iter, gamma=gamma)
            x_fgla = istft(X_fgla)
            sf.write(newpath+'%i_%s_FGLA.wav'%(c_file, snrdB), x_fgla, sr, subtype = 'PCM_24')
            
    		#Processing GLADMM
            print('GLADMM')
            X_gladmm = GLADMM(X_init, M, it=n_iter)
            x_gladmm = istft(X_gladmm)
            sf.write(newpath+'%i_%s_GLADMM.wav'%(c_file, snrdB), x_gladmm, sr, subtype = 'PCM_24')
            
        c_file+=1
        
# %%    
if __name__ == '__main__':
    main(sys.argv[1:])