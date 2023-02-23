import matplotlib.pyplot as plt
import numpy as np

from measure_process.Init_file import data_dump
from core_tools.data.ds.data_set import load_by_uuid
from scipy import integrate
import scipy


#%% 
plot_verbose = True
uuid = 1659164785501974087      
ds = load_by_uuid(uuid)

raw_init = (ds.m1_1()).ravel()
raw_read = (ds.m1_2()).ravel()
raw_total = np.concatenate((raw_init,raw_read))

histogram  = plt.hist(raw_total, bins = int(np.sqrt(len(raw_total))/10), alpha=0.4, label='data', density=True)
hist=histogram[0]
bins=histogram[1]
bins = (bins[:-1] + bins[1:]) / 2

X,Y = bins, hist

plt.show()
#%% initial fit 
from scipy.optimize import curve_fit

def gaussian(x,mu,sig):
    return (1/(np.sqrt(2*np.pi)*sig))*np.exp(-(x-mu)**2 /(2*sig**2))

def double_gaussian(x, prob_S, mu_1, sig_1, mu_2,sig_2):
    return prob_S*gaussian(x, mu_1, sig_1) + (1-prob_S)*gaussian(x, mu_2,sig_2)

# Define the initial parameter values and bounds

# initial_params = [0.4, -90,9, -125, 8]
initial_params = [0.4, -105,9, -110, 8]
bound = ([0.1, -120,0.1, -120, 0.1],[0.8, -100,20, -100, 20])
raw_fit, pcov = curve_fit(double_gaussian, X, Y, p0=initial_params, bounds = bound)

if plot_verbose:
    plt.plot(X,raw_fit[0]*gaussian(X,*raw_fit[1:3]), label = 'raw_fit S')
    plt.plot(X,(1-raw_fit[0])*gaussian(X,*raw_fit[3:]), label = 'raw_fit T')
plt.legend()

#%% fit with decays
t = 40e-6
T1 =10e-6
sampling_rate = 1e9
n_samples = round(sampling_rate*t)
n_T = T1/(1/sampling_rate)

def prob_decay_r(n,n_T):
    return np.exp(-n/n_T)

def integrand_T(s,x,mu_S,sig_S,mu_T,sig_T, n_T, n_r):
    return gaussian(x,mu_T,sig_T)*(prob_decay_r(n_r,n_T)/n_r)+ ((prob_decay_r(s,n_T)/n_T)*
            gaussian(x, (((s/n_r)*mu_T) +(((n_r-s)/n_r)*mu_S)), np.sqrt((((s/n_r)*sig_T)**2 +(((n_r-s)/n_r)*sig_S)**2))))

def integral(x,mu_S,sig_S,mu_T,sig_T, n_T, n_r):
    a, b= 0, n_r
    return scipy.integrate.quad(integrand_T,a,b, args=(x,mu_S,sig_S,mu_T,sig_T, n_T, n_r))[0]


def C_T(x,mu_S,sig_S,mu_T,sig_T, n_T, n_r):
    cc =np.empty((len(x)))
    for ii, x_s in  enumerate(x):
        rr = integral(x_s,mu_S,sig_S,mu_T,sig_T, n_T, n_r)
        cc[ii] = rr
    return np.array(cc)

def model_final(x,prob_S,mu_S,sig_S,mu_T,sig_T, n_T,n_r):
    return prob_S*gaussian(x,mu_S,sig_S) + (1-prob_S)*C_T(x,mu_S,sig_S,mu_T,sig_T, n_T, n_r)

if plot_verbose:
    plt.plot(X,model_final(X,*raw_fit, n_T, n_samples), label='Model_raw', alpha = 0.8, linewidth=2)


#%%
def model_final_integral(x,prob_S,mu_S,sig_S,mu_T,sig_T, T1):
    sampling_rate = 1e9
    n_T = T1/(1/sampling_rate)
    n_r = n_samples
    def prob_decay_r(n,n_T):
        return np.exp(-n/n_T)

    def integrand_T(s,x,mu_S,sig_S,mu_T,sig_T, n_T, n_r):
        return gaussian(x,mu_T,sig_T)*(prob_decay_r(n_r,n_T)/n_r)+ ((prob_decay_r(s,n_T)/n_T)*
                gaussian(x, (((s/n_r)*mu_T) +(((n_r-s)/n_r)*mu_S)), np.sqrt((((s/n_r)*sig_T)**2 +(((n_r-s)/n_r)*sig_S)**2))))

    def integral(x,mu_S,sig_S,mu_T,sig_T, n_T, n_r):
        a, b= 0, n_r
        return scipy.integrate.quad(integrand_T,a,b, args=(x,mu_S,sig_S,mu_T,sig_T, n_T, n_r))[0]


    def C_T(x,mu_S,sig_S,mu_T,sig_T, n_T, n_r):
        cc =np.empty((len(x)))
        for ii, x_s in  enumerate(x):
            rr = integral(x_s,mu_S,sig_S,mu_T,sig_T, n_T, n_r)
            cc[ii] = rr
        return np.array(cc)    
    
    return prob_S*gaussian(x,mu_S,sig_S) + (1-prob_S)*C_T(x,mu_S,sig_S,mu_T,sig_T, n_T, n_r)


popt, pcov = scipy.optimize.curve_fit(model_final_integral, X, Y, p0=np.concatenate((raw_fit,[T1])))
plt.plot(X,model_final_integral(X,*popt), label = 'Final Fit', alpha=0.7, linewidth=4)
plt.legend()
plt.show()
perr = np.sqrt(np.diag(pcov))
if plot_verbose:
    
    plt.plot(X,popt[0]*gaussian(X,*popt[1:3]), label = 'raw_fit2 S')
    plt.plot(X,(1-popt[0])*gaussian(X,*popt[3:-1]), label = 'raw_fit2 T')
    plt.legend()

    for ii in range(len(popt)):
        print(f'{round(popt[ii],4)} +- {round(perr[ii],4)}')
print(f'T1 time = {popt[-1]*1e6}us')



