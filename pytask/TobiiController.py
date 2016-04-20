#!/usr/bin/python
#
# Tobii Glasses controller for PsychoPy
# author: Shariq Iqbal
#

import sys
import time
import threading
import urllib2
import json
import socket
import glob
import serial
from psychopy import core
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import math
from scipy.stats import norm

sns.set_style('darkgrid')
sns.set_context('talk', font_scale=1.4)
colors = sns.color_palette("Set2")

GLASSES_IP = "192.168.71.50"  # IPv4 address
PORT = 49152
base_url = 'http://' + GLASSES_IP

# Keep-alive message content used to request live data and live video streams
KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"some_GUID\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"some_other_GUID\", \"op\": \"start\"}"


class TobiiController:

    def __init__(self):
        peer = (GLASSES_IP, PORT)
        self.data_socket = self.mksock(peer)
        td = threading.Thread(
            target=self.send_keepalive_msg, args=[self.data_socket, KA_DATA_MSG, peer])
        td.daemon = True
        td.start()

        # Create socket which will send a keep alive message for the live video
        # stream
        self.video_socket = self.mksock(peer)
        tv = threading.Thread(
            target=self.send_keepalive_msg, args=[self.video_socket, KA_VIDEO_MSG, peer])
        tv.daemon = True
        tv.start()

        try:
            self.create_project()
            self.create_participant()
        except:
            print "Could not connect to Tobii Glasses"
            sys.exit()

        self.sample_rate = 50
        self.events = []
        self.eventData = {}
        self.datafile = None

    # Create UDP socket
    def mksock(self, peer):
        iptype = socket.AF_INET
        if ':' in peer[0]:
            iptype = socket.AF_INET6
        return socket.socket(iptype, socket.SOCK_DGRAM)

    # Callback function
    def send_keepalive_msg(self, socket, msg, peer):
        while True:
            socket.sendto(msg, peer)
            time.sleep(1.0)

    def post_request(self, api_action, data=None):
        url = base_url + api_action
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')
        data = json.dumps(data)
        response = urllib2.urlopen(req, data)
        data = response.read()
        json_data = json.loads(data)
        return json_data

    def get_request(self, api_action):
        url = base_url + api_action
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req)
        data = response.read()
        json_data = json.loads(data)
        return json_data

    def wait_for_status(self, api_action, key, values):
        url = base_url + api_action
        running = True
        while running:
            req = urllib2.Request(url)
            req.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(req, None)
            data = response.read()
            json_data = json.loads(data)
            if json_data[key] in values:
                running = False
            time.sleep(1)

        return json_data[key]

    def create_project(self):
        json_data = self.post_request('/api/projects')
        self.project_id = json_data['pr_id']

    def create_participant(self):
        data = {'pa_project': self.project_id}
        json_data = self.post_request('/api/participants', data)
        self.participant_id = json_data['pa_id']

    def create_calibration(self):
        data = {'ca_project': self.project_id, 'ca_type': 'default',
                'ca_participant': self.participant_id}
        json_data = self.post_request('/api/calibrations', data)
        self.calibration_id = json_data['ca_id']

    def start_calibration(self):
        self.post_request(
            '/api/calibrations/' + self.calibration_id + '/start')

    def create_recording(self):
        data = {'rec_participant': self.participant_id}
        json_data = self.post_request('/api/recordings', data)
        self.recording_id = json_data['rec_id']

    def start_recording(self):
        self.post_request('/api/recordings/' + self.recording_id + '/start')

    def stop_recording(self):
        self.post_request('/api/recordings/' + self.recording_id + '/stop')

    def waitForFindEyeTracker(self):
        while len(self.eyetrackers.keys()) == 0:
            time.sleep(0.01)

    ##########################################################################
    # tracking methods
    ##########################################################################
    def startTracking(self):
        self.eventData = {}
        self.events = []
        self.sync_pulses = []
        self.pupil_data = []
        self.start_sync()
        self.start_data_stream()
        self.start_recording()

    def stopTracking(self):
        self.stop_recording()
        self.stop_data_stream()
        self.stop_sync()
        if self.datafile is None:
            print 'Data file is not set.'
        else:
            if len(self.sync_pulses) > 0:
                self.eventData['sync_pulses'] = self.sync_pulses
            else:  # write streamed gaze data if sync pulses not present
                self.eventData['pupil_data'] = self.pupil_data
            self.datafile.write(json.dumps(self.eventData))
            self.datafile.flush()

    def start_data_stream(self):
        '''
        Streams data and records pupil response
        '''
        self.pupil_stop = threading.Event()
        try:
            th = threading.Thread(target=self.get_data)
            th.daemon = True
            th.start()
        except (KeyboardInterrupt, SystemExit):
            self.stopLiveCheck()

    def stop_data_stream(self):
        self.pupil_stop.set()

    def get_data(self):
        while not self.pupil_stop.is_set():
            raw_data, address = self.data_socket.recvfrom(1024)
            try:
                data = json.loads(raw_data)
                if 'pd' in data and data['eye'] == 'left':
                    if data['s'] == 0:
                        self.pupil_data.append((core.getTime(), data['pd']))
                    else:
                        self.pupil_data.append((core.getTime(), np.nan))
            except:
                pass

    # starts thread to listen to sync port of Tobii Glasses and record pulses
    def start_sync(self):
        self.sync_stop = threading.Event()
        try:
            th = threading.Thread(target=self.get_pulses)
            th.daemon = True
            th.start()
        except (KeyboardInterrupt, SystemExit):
            self.stop_sync()

    def stop_sync(self):
        self.sync_stop.set()

    def get_pulses(self):
        try:
            port = glob.glob('/dev/cu.usbserial*')[0]  # assume first USB Serial
        except IndexError:
            print "Sync pulse input not found."
            return
        ser = serial.Serial(port, 38400)
        while not self.sync_stop.is_set():
            s = ser.read()  # blocks until data arrives
            if len(s) > 0:
                self.sync_pulses.append(core.getTime())
        ser.close()

    def print_whole_fig(self, filename, time_name, relvar_mask):
        """
        Plots an entire pupil time series with responses to two classes
        of stimuli (usually 'target' and 'other') marked with different
        colored lines.
        filename (str): path/location to place generated plot
        time_name (str): name of vector that contains timestamps for events
                         (NOTE: this vector must be set by setVector before
                         plot can be generated)
        relvar_mask (str): name of vector that indicates which class each
                          event is in (1 = target, 0 = other)
        """
        pupil_array = np.array(self.pupil_data)
        clean_size = self.cleanseries(pd.Series(pupil_array[:, 1])).values
        plt.plot(pupil_array[:, 0], clean_size)
        stim_time = self.eventData[time_name]
        trial_mask = self.eventData[relvar_mask]
        targets = np.extract(trial_mask, stim_time)
        other = np.extract(np.logical_not(trial_mask), stim_time)
        plt.vlines(targets, np.nanmin(clean_size), np.nanmax(clean_size),
                   colors='red')
        plt.vlines(other, np.nanmin(clean_size), np.nanmax(clean_size),
                   colors='green')

        plt.title('Whole Trial Pupil Size for ' + self.eventData['task'])
        plt.ylabel('Pupil Size (mm)')
        plt.xlabel('Time (sec)')
        plt.savefig(filename, bbox_inches='tight')
        core.wait(1.0)  # let file finish writing
        plt.gcf().clear()

    def print_marked_fig(self, filename, event_names):
        """
        Plots an entire pupil time series with events marked by vertical lines.
        filename (str): path/location to place generated plot
        event_names (list of str): List of event names to be marked on the plot
        """
        pupil_array = np.array(self.pupil_data)
        clean_size = self.cleanseries(pd.Series(pupil_array[:, 1])).values
        plt.plot(pupil_array[:, 0], clean_size)
        colors = sns.color_palette('hls', n_colors=len(event_names))
        i = 0
        for name in event_names:
            plt.vlines(self.eventData[name], np.nanmin(clean_size),
                       np.nanmax(clean_size), colors=colors[i],
                       label=name)
            i += 1

        plt.title('Whole Trial Pupil Size for ' + self.eventData['task'])
        plt.ylabel('Pupil Size (mm)')
        plt.xlabel('Time (sec)')
        plt.legend()
        plt.savefig(filename, bbox_inches='tight')
        core.wait(1.0)  # let file finish writing
        plt.gcf().clear()


    def print_fig(self, filename, time_name, relvar_mask, tpre=1.0, tpost=2.5):
        """
        Generates a figure for pupillary response to two classes
        of stimuli (usually 'target' and 'other')
        filename (str): path/location to place generated plot
        time_name (str): name of vector that contains timestamps for events
                         (NOTE: this vector must be set by setVector before
                         plot can be generated)
        relvar_mask (str): name of vector that indicates which class each
                          event is in (1 = target, 0 = other)
        tpre (float): time before each stim starts to slice
        tpost (float): time after each stim starts to slice
        """
        pupil_array = np.array(self.pupil_data)
        stim_time = self.eventData[time_name]
        trial_mask = self.eventData[relvar_mask]
        pupil_time = pupil_array[:, 0]
        pupil_diam = self.cleanseries(pd.Series(pupil_array[:, 1])).values
        targ_trials = []
        other_trials = []

        currEventIndex = 0
        for i in range(len(pupil_time)):
            t = pupil_time[i]
            if t > stim_time[currEventIndex]:  # we have reached the next event
                chunk = self.get_chunk(i, pupil_diam, tpre, tpost)
                # if able to get a good slice (no IndexError)
                if chunk is not None:
                    if trial_mask[currEventIndex] == 1.0:  # event is target
                        targ_trials.append(chunk)
                    elif trial_mask[currEventIndex] == 0.0:  # event is other
                        other_trials.append(chunk)
                currEventIndex += 1
                if currEventIndex >= len(stim_time):
                    break
        targ_trials = np.array(targ_trials)
        other_trials = np.array(other_trials)

        # Normalize each trial with tpre region if it exists
        if tpre != 0:
            cutoff = self.sample_rate * tpre
            targ_trials = targ_trials - \
                np.tile(targ_trials[:, :cutoff].mean(axis=1).reshape(
                    (targ_trials.shape[0], 1)), targ_trials.shape[1])
            other_trials = other_trials - \
                np.tile(other_trials[:, :cutoff].mean(axis=1).reshape(
                    (other_trials.shape[0], 1)), other_trials.shape[1])

        self.plot_with_sem(targ_trials, colors[1])
        self.plot_with_sem(other_trials, colors[0])

        plt.title('Pupillary response for ' + self.eventData['task'])
        plt.ylabel('Normalized Pupil Size (arbitrary units)')
        plt.xlabel('Time (samples)')
        plt.legend(['Target', 'Other'], bbox_to_anchor=(
            1.05, 1), loc=2, borderaxespad=0.)
        plt.savefig(filename, bbox_inches='tight')
        core.wait(1.0)  # let file finish writing
        plt.gcf().clear()

    def gauss_convolve(self, x, sigma):
        edge = int(math.ceil(5 * sigma))
        fltr = norm.pdf(range(-edge, edge), loc=0, scale=sigma)
        fltr = fltr / sum(fltr)

        buff = np.ones((1, edge))[0]

        szx = x.size

        xx = np.append((buff * x[0]), x)
        xx = np.append(xx, (buff * x[-1]))

        y = np.convolve(xx, fltr, mode='valid')
        y = y[:szx]
        return y

    def plot_with_sem(self, x, color):
        ntrials = x.shape[0]
        smwid = 2
        bin_t = np.array(range(x.shape[1]))

        xm = x.mean(axis=0)
        sd = x.std(axis=0)
        effsamp = np.sum(np.logical_not(np.isnan(x)), 0)
        sem = sd / np.sqrt(effsamp)
        sem = list(sem)

        xsm = self.gauss_convolve(xm, smwid)
        xhi = self.gauss_convolve(xm + sem, smwid)
        xlo = self.gauss_convolve(xm - sem, smwid)

        plt.hold(True)
        x_ptch = np.append(bin_t, bin_t[::-1])
        y_ptch = np.append(xlo, xhi[::-1])

        if ntrials > 1:
            plt.fill(
                x_ptch, y_ptch, color=color, alpha=0.25, edgecolor=None)

        plt.plot(bin_t, xsm, color=color, linewidth=2.0)
        plt.hold(False)

    def get_chunk(self, i, data, tpre, tpost):
        """
        Returns a slice from data, starting before index i by tpre seconds
        and ending after by tpost seconds.
        """
        sr = self.sample_rate
        try:
            if i + int(sr * tpost) > len(data):
                return np.hstack((data[i - int(sr * tpre):],
                                  np.ones(i + int(sr * tpost) - len(data)) * data[i - int(sr * tpre):].mean()))
            else:
                return data[i - int(sr * tpre):i + int(sr * tpost)]
        except IndexError:
            return None

    def window_diff(self, data, width):
        """
        Takes a series and calculates a diff between each value and the mean of
        values surrounding it (dictated by width) If this window extends past the
        data's indices, it will ignore those values.
        """
        diff = data.copy()
        for i in range(len(data)):
            if i < width:
                win_m = (data[:i].mean() + data[i+1:i+1+width].mean())/2
            else:
                win_m = (data[i-width:i].mean() + data[i+1:i+1+width].mean())/2
            diff[i] -= win_m
        return diff

    def cleanseries(self, data):
        bad = (data == np.nan)

        dd = self.window_diff(data, 10)
        sig = np.nanmedian(np.absolute(dd) / 0.67449)
        th = 5
        disc = np.absolute(dd) > th * sig

        to_remove = np.nonzero(bad | disc)[0]
        up_one = range(len(to_remove))
        for i in range(len(to_remove)):
            up_one[i] = to_remove[i] + 1
        down_one = range(len(to_remove))
        for i in range(len(to_remove)):
            down_one[i] = to_remove[i] - 1
        isolated = np.intersect1d(up_one, down_one)

        allbad = np.union1d(to_remove, isolated)

        newdat = data.copy()
        newdat[allbad] = np.nan

        goodinds = np.nonzero(np.invert(np.isnan(newdat)))[0]
        if len(goodinds) == 0:
            print "Not enough good data to clean. Aborting."
            return data
        else:
            return pd.Series.interpolate(newdat, method='linear')

    # altered to take open file instead of filename. got rid of header which
    # makes the file incompatible with matlab
    def setDataFile(self, openfile):
        self.datafile = openfile

    def recordEvent(self, event):  # records timestamp for an event
        self.eventData[event].append(core.getTime())

    def addParam(self, param, value):  # appends value to param list
        self.eventData[param].append(value)

    def setParam(self, param, value):  # sets value for param
        self.eventData[param] = value

    def setVector(self, param, vector):  # sets a vector in an event parameter
        self.eventData[param] = list(vector)

    # creates columns for events and params
    def setEventsAndParams(self, events):
        self.events = events
        for event in events:
            self.eventData[event] = []

    def flushData(self):
        self.eventData = {}
        self.events = []
        self.sync_pulses = []
        self.pupil_data = []
