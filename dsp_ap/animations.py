import math
import numpy as np
from matplotlib import animation
import matplotlib.pyplot as plt
from IPython.display import display, HTML
from .signals import get_samples_and_rate, get_both_samples_and_rate


def sine_approx(signal, samplerate=None, include_cosines=False, controls=True, min_freq=0, figsize=(12, 6), title='', fps=5):
    samples, samplerate = get_samples_and_rate(signal, samplerate)
    num_samples = len(samples)
    timepoints = np.arange(num_samples) / samplerate
    
    if min_freq == 0:
        min_freq = samplerate / num_samples
    
    num_freqs = math.ceil((samplerate / 2) / min_freq) + 1
    
    freqs = np.empty(num_freqs)
    sin_corr = np.empty(num_freqs)
    cos_corr = np.empty(num_freqs)
    cumul = np.zeros(num_samples)
    
    fig, axes = plt.subplots(2, figsize=figsize)
    fig.suptitle(title)
    fig.subplots_adjust(hspace=0.4)
    
    sine_components, = axes[0].plot([], [], lw=2, marker='s', linestyle='None', color='C0')
    cosine_components, = axes[0].plot([], [], lw=2, marker='o', linestyle='None', color='C1')
    progress = axes[0].axvline(0, color='k')
    axes[0].set_xlim((0, samplerate / 2))
    if include_cosines:
        axes[0].set_xlabel('frequencies of sine and cosine components [Hz]')
        axes[0].legend([sine_components, cosine_components], ['sines', 'cosines'], loc='upper right', frameon=False)
    else:
        axes[0].set_xlabel('frequencies of sine components [Hz]')
    axes[0].set_ylim((-1.1, 1.3))
    axes[0].set_ylabel('correlation coefficient')
    label = axes[0].text(0.2, 1.11, '')
    
    axes[1].plot(timepoints, samples, lw=2, color='C2')
    approx, = axes[1].plot([], [], lw=2, color='C3')
    axes[1].set_xlim((0, timepoints[-1]))
    axes[1].set_xlabel('time [s]')
    axes[1].set_ylim((-1.2, 1.2))
    axes[1].set_ylabel('amplitude')

    def animate(i):
        # compute contribution of current sinusoidal component to signal
        freqs[i] = min_freq * i
        cur_sin = np.sin(2*np.pi*freqs[i]*timepoints)
        sin_corr[i] = np.correlate(cur_sin, samples) / (num_samples / 2)
        nonlocal cumul
        cumul += sin_corr[i] * cur_sin
        if include_cosines:
            cur_cos = np.cos(2*np.pi*freqs[i]*timepoints)
            cos_corr[i] = np.correlate(cur_cos, samples) / (num_samples / 2)
            cumul += cos_corr[i] * cur_cos

        
        # plot
        if include_cosines:
            x_offset = samplerate / 2 / num_freqs / 10 # offset of 1/10th of inter-marker distance to avoid overlapping markers
            sine_components.set_data(freqs[:i+1]-x_offset, sin_corr[:i+1])
            cosine_components.set_data(freqs[:i+1]+x_offset, cos_corr[:i+1])
            label.set_text('{} Hz, sin corr {:.3f}, cos corr {:.3f}'.format(freqs[i], sin_corr[i], cos_corr[i]))
        else:
            sine_components.set_data(freqs[:i+1], sin_corr[:i+1])
            label.set_text('{} Hz, sin corr {:.3f}'.format(freqs[i], sin_corr[i]))
#         update_stemcontainer_lc(stems, output[:i])
        progress.set_data([freqs[i], freqs[i]], [0, 1])
        approx.set_data(timepoints, cumul)
        return (sine_components, cosine_components, progress, approx, label)
    
    anim = animation.FuncAnimation(fig, animate, frames=num_freqs, interval=1000/fps, blit=True, repeat=False)
    if controls:
        display(HTML(anim.to_jshtml()))
    else:
        display(HTML(anim.to_html5_video()))
    plt.close(fig)


def autocorrelate(signal, samplerate=None, controls=True, min_freq=0, figsize=(12, 6), title='', fps=5):
    crosscorrelate(signal, signal, samplerate=samplerate, controls=controls, min_freq=min_freq, figsize=figsize, legend=['original signal', 'time-shifted copy'], title=title, fps=fps)


def crosscorrelate(signal1, signal2, samplerate=None, controls=True, min_freq=0, figsize=(12, 6), legend=['signal1', 'signal2'], title='', fps=5):
    longest_samples, shortest_samples, samplerate = get_both_samples_and_rate(signal1, signal2, samplerate)
    longest_length = len(longest_samples)
    shortest_length = len(shortest_samples)
    if shortest_length > longest_length:
        swapped = True
        longest_samples, shortest_samples = shortest_samples, longest_samples
        longest_length, shortest_length = shortest_length, longest_length
    else:
        swapped = False
    lags = np.arange(-shortest_length+1, longest_length)
    num_lags = len(lags)
    acrs = np.correlate(longest_samples, shortest_samples, mode='full')
    
    fig, axes = plt.subplots(2, figsize=figsize)
    fig.suptitle(title)
    fig.subplots_adjust(hspace=0.4)
    
    axes[0].set_xlim((-shortest_length, longest_length))
    axes[0].set_xlabel('lags')
    axes[0].set_ylim((-1.1, 1.3))
    axes[0].set_ylabel('amplitude')
    longest_waveform, = axes[0].plot(np.arange(longest_length), longest_samples, lw=2, color='C0')
    shortest_waveform, = axes[0].plot([], [], lw=2, color='C1')
    if swapped:
        legend_order = [shortest_waveform, longest_waveform]
    else:
        legend_order = [longest_waveform, shortest_waveform]
    axes[0].legend(legend_order, legend, loc='upper right', frameon=False, ncol=2)
    progress = axes[0].axvline(0, color='k')
    label = axes[0].text(-shortest_length+1, 1.11, '')
    
    acr_plot, = axes[1].plot([], [], lw=2, color='C2')
    axes[1].set_xlim((-shortest_length, longest_length))
    axes[1].set_xlabel('lags')
    axes[1].set_ylim((np.amin(acrs), np.amax(acrs)))
    axes[1].set_ylabel('amplitude')

    def animate(i):
        shortest_waveform.set_data(np.arange(lags[i], lags[i]+shortest_length), shortest_samples)
        period = lags[i] / samplerate
        freq = 1 / period if period != 0 else 0
        label.set_text('lag: {}, acr: {:.3f}, period: {:.3f} s, freq: {:.3f} Hz'.format(lags[i], acrs[i], period, freq))
        progress.set_data([lags[i], lags[i]], [0, 1])
        acr_plot.set_data(lags[:i+1], acrs[:i+1])
        return (shortest_waveform, acr_plot, progress, label)
    
    anim = animation.FuncAnimation(fig, animate, frames=np.arange(num_lags), interval=1000/fps, blit=True, repeat=False)
    if controls:
        display(HTML(anim.to_jshtml()))
    else:
        display(HTML(anim.to_html5_video()))
    plt.close(fig)
