import os.path

from mpl_toolkits.mplot3d.art3d import Line3D

print("GUI script initialised...")
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter.simpledialog import askstring
from tkinter import *
import xml.etree.ElementTree as ET
import xml.dom.minidom as md
import subprocess
import shutil
import time
import h5py
import numpy as np
from scipy.signal import chirp
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import psutil

# global variables
entry_count = 0
sim_name = ""
load_tree = ""
entry_values = []
label_names = []
ev_text = []
root = ET.Element("simulation")
antenna_list = []
pulse_list = []
timing_list = []
delete_element_list = []
root_elements = []
motionP_element = 0
plat_element = 0
globalprf = 0
prop_speed = 0
fersxml_results = ""
h5_results = ""
wsl_shared_directory = 'C:/Program Files/wsl_share'
dummy = ""
load_test = False
sim_times = []
cpu_usage = []
mem_usage = []
wsl_dir = ""
ichunks = []
qchunks = []
ichunks_data = []
qchunks_data = []
testlist_I = []
testlist_Q = []

x_loc = []
y_loc = []
z_loc = []
pw_time = []

def get_c():
    return float(prop_speed)

def get_prf():
    return float(globalprf)

def get_xml_root():
    global root
    return ET.ElementTree(root).getroot()

def add_label(root, name, row, col, type=None):
    if type == "header":
        ttk.Label(root, text=name, anchor="w", font='bold').grid(row=row, column=col, sticky='w', columnspan=2)

    else:
        ttk.Label(root, text=name, anchor="w").grid(row=row, column=col, sticky='w')


def append_entry_values(item):
    global entry_values
    entry_values.append(item)

def get_entry_values():
    return entry_values

def read_entry_values():
    global ev_text
    for entry in entry_values:
        x = entry.get()
        ev_text.append(x)
    return ev_text


def add_entry(root, r, c, default=None):
    global entry_values
    if default is None:
        ent = tk.Entry(root)
        ent.grid(row=r, column=c)
        append_entry_values(ent)
    else:
        ent = tk.Entry(root)
        ent.grid(row=r, column=c)
        ent.insert(0, default)
        append_entry_values(ent)

    return ent

def clear_entry(entry, entry2=None, entry3=None, entry4=None, entry5=None):
    entry.delete(0,'end')
    if entry2 is not None:
        entry2.delete(0,'end')
    if entry3 is not None:
        entry3.delete(0,'end')
    if entry4 is not None:
        entry4.delete(0,'end')
    if entry5 is not None:
        entry5.delete(0,'end')

def test():
    x = get_entry_values()
    d = {}
    for entry in x:
        fn = entry.cget("text")
        fv = entry.get()
        d[fn] = fv
    return x


def write_data():
    f = open("test1.txt", "w")
    x = get_entry_values()
    try:
        for entry in x:
            data = entry.get()
            f.write(data + '\n')
        print("data written successfully")
    except Exception as e:
        print(f"Error writing to file: {str(e)}")

    f.close()


# ATTEMPTING TO MAKE SOME XML CONVERSION FUNCTIONS

def make_dict(labels, entries):
    print("done")
    data = {}
    for label, entry in zip(labels, entries):
        value = entry.get()
        data[label] = value
    return data


def to_xml2(data):
    root = ET.Element("data")
    for fn, fv in data.items():
        f_element = ET.SubElement(root, fn)
        f_element.text = fv

    tree = ET.ElementTree(root)
    xml_data = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
    # return ET.tostring(root, encoding="utf-8").decode("utf-8")
    return xml_data


def to_xml(data):
    # creating root element
    root = md.Document()
    data_element = root.createElement("data")
    root.appendChild(data_element)

    # creating child elements
    for fn, fv in data.items():
        field_element = root.createElement(fn)
        field_text = root.createTextNode(str(fv))
        field_element.appendChild(field_text)
        data_element.appendChild(field_element)

    return root.toprettyxml(indent="  ")


def save_xml(labels, entries):
    data = make_dict(labels, entries)
    xml_data = to_xml(data)
    with open("txml.xml", "w") as file:
        file.write(xml_data)
    print("save succ")

def make_pulse_element(root, name, filename, power=None, carrier=None, length=None, rate=None):
    pulse_element = ET.SubElement(root, "pulse")
    pulse_element.set("name", name)
    pulse_element.set("type", "file")
    pulse_element.set("filename", filename)

    if length is not None:
        length_element = ET.SubElement(pulse_element, "length")
        length_element.text = str(length)

    if rate is not None:
        rate_element = ET.SubElement(pulse_element, "rate")
        rate_element.text = str(rate)

    if power is not None:
        power_element = ET.SubElement(pulse_element, "power")
        power_element.text = str(power)

    if carrier is not None:
        carrier_element = ET.SubElement(pulse_element, "carrier")
        carrier_element.text = str(carrier)

    return pulse_element

def make_tree(name):
    global root
    root.set("name", name)
    return ET.ElementTree(root)

def set_root_name():
    return dummy
def timing_source(root, name, frequency, jitter, freq_offset=None):
    timing_element = ET.SubElement(root, "timing")
    timing_element.set("name", name)

    freq_element = ET.SubElement(timing_element, "frequency")
    freq_element.text = str(frequency)

    jitter_element = ET.SubElement(timing_element, "jitter")
    jitter_element.text = str(jitter)

    if freq_offset is not None:
        off_element = ET.SubElement(timing_element, "freq_offset")
        off_element.text = str(freq_offset)

    return timing_element
def make_antenna(root, name, pattern):
    antenna_element = ET.SubElement(root, "antenna")
    antenna_element.set("name", name)
    antenna_element.set("pattern", pattern)

    return antenna_element

def make_fixed_rotation(root, startA, startE, azimuthrate, elevationrate):
    fr_element = ET.SubElement(root, "fixedrotation")
    start_azimuth_element = ET.SubElement(fr_element, "startazimuth")
    start_azimuth_element.text = str(startA)
    start_elevation_element = ET.SubElement(fr_element, "startelevation")
    start_elevation_element.text = str(startE)
    aRate_element = ET.SubElement(fr_element, "azimuthrate")
    aRate_element.text = str(azimuthrate)
    eRate_element = ET.SubElement(fr_element, "elevationrate")
    eRate_element.text = str(elevationrate)

def make_rotation_path(root, LorC, azimuth, elev, time):
    rp_element = ET.SubElement(root, "rotationpath")
    rp_element.set("rotationinterpolation", LorC)
    rp_wp_element = ET.SubElement(rp_element, "rotationwaypoint")
    azimuth_element = ET.SubElement(rp_wp_element, "azimuth")
    azimuth_element.text = str(azimuth)
    elevation_element = ET.SubElement(rp_wp_element, "elevation")
    elevation_element.text = str(elev)
    time_element = ET.SubElement(rp_wp_element, "time")
    time_element.text = str(time)

def make_monostatic(root, name, type, antenna, pulse, timing, prf=None, noise_temp=None, window_skip=None, window_length=None):
    mono_element = ET.SubElement(root, "monostatic")
    mono_element.set("name", name)
    mono_element.set("type", type)
    mono_element.set("antenna", antenna)
    mono_element.set("pulse", pulse)
    mono_element.set("timing", timing)

    if prf is not None:
        prf_element = ET.SubElement(mono_element, "prf")
        prf_element.text = str(prf)

    if noise_temp is not None:
        noise_temp_element = ET.SubElement(mono_element, "noise_temp")
        noise_temp_element.text = str(noise_temp)

    if window_skip is not None:
        win_skip_element = ET.SubElement(mono_element, "window_skip")
        win_skip_element.text = str(window_skip)

    if window_length is not None:
        win_len_element = ET.SubElement(mono_element, "window_length")
        win_len_element.text = str(window_length)

def make_transmitter(root, name, prf, type, pulse, antenna, timing):
    transmitter_element = ET.SubElement(root, "transmitter")
    transmitter_element.set("name", name)
    transmitter_element.set("type", type)
    transmitter_element.set("pulse", pulse)
    transmitter_element.set("antenna", antenna)
    transmitter_element.set("timing", timing)
    prf_element = ET.SubElement(transmitter_element, "prf")
    prf_element.text = str(prf)

def make_receiver(root, name, antenna, timing, window_skip, window_length):
    receiver_element = ET.SubElement(root, "receiver")
    receiver_element.set("name", name)
    receiver_element.set("antenna", antenna)
    receiver_element.set("timing", timing)
    win_skip_element = ET.SubElement(receiver_element, "window_skip")
    win_skip_element.text = str(window_skip)
    win_len_element = ET.SubElement(receiver_element, "window_length")
    win_len_element.text = str(window_length)

def make_target(root, name, value, type):
    target_element = ET.SubElement(root, "target")
    target_element.set("name", name)
    rcs_element = ET.SubElement(target_element, "rcs")
    rcs_element.set("type", type)
    value_element = ET.SubElement(rcs_element, "value")
    value_element.text = str(value)

def make_platform(root, name, mchoice, x, y, alt, time):
    global motionP_element
    global plat_element
    plat_element = ET.SubElement(root, "platform")
    plat_element.set("name", name)
    #motionpath
    motionP_element = ET.SubElement(plat_element, "motionpath")
    motionP_element.set("interpolation", mchoice)
    position_element = ET.SubElement(motionP_element, "positionwaypoint")

    x_element = ET.SubElement(position_element, "x")
    x_element.text = str(x)

    y_element = ET.SubElement(position_element, "y")
    y_element.text = str(y)

    alt_element = ET.SubElement(position_element, "altitude")
    alt_element.text = str(alt)

    time_element = ET.SubElement(position_element, "time")
    time_element.text = str(time)

    #return ET.ElementTree(plat_element)
    return plat_element
    #fixedrotation
    #monostatic
def make_position_element(x, y, altitude, time):
    pos_element = ET.SubElement(motionP_element, "positionwaypoint")

    x_element = ET.SubElement(pos_element, "x")
    x_element.text = str(x)

    y_element = ET.SubElement(pos_element, "y")
    y_element.text = str(y)

    alt_element = ET.SubElement(pos_element, "altitude")
    alt_element.text = str(altitude)

    time_element = ET.SubElement(pos_element, "time")
    time_element.text = str(time)

    return pos_element
def create_xml(root, starttime, endtime, c, rate, xml, csv, binary, csvbinary):

    #Sub elements
    parameters_element = ET.SubElement(root, "parameters")

    # elements of parameters
    starttime_element = ET.SubElement(parameters_element, "starttime")
    starttime_element.text = str(starttime)

    endtime_element = ET.SubElement(parameters_element, "endtime")
    endtime_element.text = str(endtime)

    c_element = ET.SubElement(parameters_element, "c")
    c_element.text = str(c)

    rate_element = ET.SubElement(parameters_element, "rate")
    rate_element.text = str(rate)

    export_element = ET.SubElement(parameters_element, "export")
    if csv == "0":
        export_element.set("csv", "false")
    else:
        export_element.set("csv", "true")
    if binary == "0":
        export_element.set("binary", "false")
    else:
        export_element.set("binary", "true")
    if csvbinary == "1":
        export_element.set("csvbinary", "true")
    else:
        export_element.set("csvbinary", "false")
    if xml == "1":
        export_element.set("xml", "true")
    else:
        export_element.set("xml", "false")

    return parameters_element

def save_xml2(tree, file_path, file_path2):
    tree.write(file_path, encoding="utf-8", xml_declaration=True)
    tree.write(file_path2, encoding="utf-8", xml_declaration=True)
    #tree.write(file_path3, encoding="utf-8", xml_declaration=True)

def load_xml():
    global root_list
    global root_elements
    global sim_name
    global load_tree
    global prop_speed
    global globalprf
    global fersxml_results
    global x_loc
    global y_loc
    global z_loc
    global pw_time

    x_loc = []
    y_loc = []
    platform_count = 0
    pwaypoint_count = 0

    x_static = []
    y_static = []
    z_static = []
    t_static = []


    fp = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
    if not fp:
        return
    #fersxml_results = str(fp)
    load_tree = ET.parse(fp)
    loaded_root = load_tree.getroot()
    print(load_tree)
    sim_name = loaded_root.get("name", "")
    print("Sim name is " + str(sim_name))
    c_element = loaded_root.find(".//c")
    prf_element = loaded_root.find(".//prf")
    fig = plt.figure(figsize=(10, 7))
    ax = plt.axes(projection="3d")
    # Setting up a colour bar
    height_cmap = plt.get_cmap('hsv')

    # Locating x, y, z values for plotting co-ordinates of targets
    for platform in loaded_root.findall('.//platform'):
        platform_id = platform.get("name", "")
        print(platform_id)
        platform_count += 1
        pwaypoint_count=0
        x_loc = []
        y_loc = []
        z_loc = []
        for pwaypoint in platform.findall('.//positionwaypoint'):
            pwaypoint_count+=1
            print(pwaypoint_count)
        for value in platform.findall('.//positionwaypoint'):
            time = float(value.find('time').text)
            x = float(value.find('x').text)
            y = float(value.find('y').text)
            z = float(value.find('altitude').text)

            if pwaypoint_count == 1:
                # Append to list
                x_static.append(x)
                y_static.append(y)
                z_static.append(z)
                t_static.append(time)
                ax.scatter3D(x_static, y_static, z_static, label=str(platform_id), cmap=height_cmap)
                ax.plot(x_static, y_static, z_static, color='black')
            if pwaypoint_count > 1:
                x_loc.append(x)
                y_loc.append(y)
                z_loc.append(z)
        #plt.scatter(x_loc, y_loc, z_loc, label=str(platform_id), color='blue')
        if pwaypoint_count > 1:
            ax.scatter3D(x_loc, y_loc, z_loc, label=str(platform_id), cmap=height_cmap)
            ax.plot(x_loc, y_loc, z_loc, color='black')


    if c_element is not None:
        prop_speed = c_element.text
    print("propagation speed set to: " + str(prop_speed))

    if prf_element is not None:
        globalprf = prf_element.text
    print("PRF set to: " + str(globalprf))

    root_list.delete(0, tk.END)
    root_elements.clear()
    for element in loaded_root:
        root_list.insert(tk.END, element.tag)
        root_elements.append(element)

    print("Plotting platforms")




    ax.set_xlabel('X-axis', fontweight='bold')
    ax.set_ylabel('Y-axis', fontweight='bold')
    ax.set_zlabel('Z-axis', fontweight='bold')
    plt.grid(True)
    plt.legend()
    plt.show()

def remove_root():
    global root_list
    global root_elements
    selected_root = root_list.curselection()
    if selected_root:
        selected_root = selected_root[0]
        root_list.delete(selected_root)
        root_elements.pop(selected_root)

    print("root " + str(selected_root) + " has been removed")

def write_loaded_xml():
    global root_elements
    global sim_name
    global root_list
    print("root elements : " + str(root_elements))
    new_root = ET.Element("simulation", name=sim_name)

    for element in root_elements:
        print(element)
        new_root.append(element)

    tree = ET.ElementTree(new_root)
    new_root = tree.getroot()
    load_check = check_root_list(root_list)

    if load_check == False:
        tree.write("newxml.xml", encoding="utf-8", xml_declaration=True)
        tree.write('C:/Users/' + str(sim_name) + '.fersxml')

    if load_check == True:
        new_root.set("name", dummy)
        tree.write("newxml.xml", encoding="utf-8", xml_declaration=True)
        tree.write('C:/Users/'+str(dummy) + '.fersxml')

    print("XML file as been written")

def check_root_list(listbox):
    end = listbox.index("end")
    if end == 0:
        return False
    else:
        return True

def run_fers_wsl(file):
    global sim_times
    global cpu_usage
    global mem_usage
    time_start = time.time()

    wsl_distro_name = 'Ubuntu'
    wsl_command_list = ['/home/' + str(wsl_dir) + '/FERS/build/src/fers /mnt/c/Users/'+str(file)]
    wsl_start = ['wsl', '--distribution', wsl_distro_name]

    print("attempting bootup...")
    print("boot successful...")
    print("Executing commands...")

    for command in wsl_command_list:

        subprocess.run(['wsl.exe', '-d', wsl_distro_name, 'bash', '-c', command])
        cpu_usage.append(int(psutil.cpu_percent()))
        mem_usage.append(int(psutil.virtual_memory().percent))
        print("command " + command + " was executed successfully")




    #print("Plotting targets...")
    print("Done")
    time_end = time.time()
    fers_time = time_end - time_start

    print("Total execution time was %s seconds"%fers_time)
    sim_times.append(fers_time)

def run_sim():
    global cpu_usage
    global mem_usage
    global wsl_dir
    ask_window = tk.Tk()
    ask_window.withdraw()
    wsl_dir = askstring("User Directory", "Enter your WSL user directory name: ")

    fp = filedialog.askopenfilename(filetypes=[("XML files", "*.fersxml")])
    current_cpu_usage = psutil.cpu_percent()
    current_mem_usage = psutil.virtual_memory().percent
    print(current_cpu_usage)
    print(current_mem_usage)
    if not fp:
        return
    if fp != 'C:/Users/' + str(os.path.basename(fp)):
        shutil.copy(fp, 'C:/Users/')

    run_fers_wsl(os.path.basename(fp))

    print("shutting down WSL instance...")
    subprocess.run(['wsl.exe', '--shutdown'])
    print(np.mean(cpu_usage))
    print(np.mean(mem_usage))

    print("Average execution (s): %s"%(np.mean(sim_times)))
    print("Average CPU usage: " + str(np.mean(cpu_usage) - current_cpu_usage))
    print("Average mem usage: " + str(np.mean(mem_usage) - current_mem_usage))
    #print("Average CPU usage (%): %s" % (int(np.mean(cpu_usage)) - current_cpu_usage))
    #print("Average RAM (%): %s" % (int(np.mean(mem_usage)) - current_mem_usage))
def plot_XvT(file, c, prf):

    #tree = ET.parse('C:/Users/samja/PycharmProjects/final/' + str(file))
    tree = ET.parse(file)
    root = tree.getroot()
    print(root)
    num_responses = 0
    time_data = []
    power_data = []
    doppler_data = []
    range_data = []
    phase_data = []
    phase_deg_data = []
    amplitude_data = []
    pw = 5000e-9

    for value in root.findall('.//InterpolationPoint'):
        time = float(value.find('time').text)
        time_data.append(time)
        num_responses += 1
    dt = max(time_data) - min(time_data)
    if prf > 0:
        num_targets = num_responses / (prf * dt)
    else:
        num_targets = 1
        print("Load in an XML file to get a PRF value")

    for value in root.findall('.//InterpolationPoint'):
        i = 0
        #time = float(value.find('time').text)
        power = float(value.find('power').text)
        doppler = float(value.find('doppler').text)

        phase = float(value.find('phase').text)
        phase_deg = float(value.find('phasedeg').text)
        amp = float(value.find('amplitude').text)
        #time_data.append(time)
        power_data.append(power)
        doppler_data.append(doppler)
        phase_data.append(phase)
        phase_deg_data.append(phase_deg)
        amplitude_data.append(amp)


    print(len(time_data), len(power_data))
    dt = max(time_data) - min(time_data)
    dp = max(power_data) - min(power_data)




    print("diff in time is %s"%dt)
    print("diff in power is %s"%dp)

    return time_data, power_data, doppler_data, range_data, phase_data, phase_deg_data, amplitude_data, num_targets

def read_h5(filepath):

    ichunks_data=[]
    qchunks_data=[]
    testlist_I = []
    testlist_Q = []
    ichunks = []
    qchunks = []

    print("reading file...")
    with h5py.File(filepath, 'r') as hf:
        print(list(hf.keys()))
        all_chunks = list(hf.keys())
        # group chunk data sets into separate lists
        for key in all_chunks:
            if key[-1] == "I":
                ichunks.append(key)
            else:
                qchunks.append(key)
        testlist_I = hf[ichunks[0]][:]
        testlist_Q = hf[ichunks[1]][:]

        # add chunk data to data lists
        for chunk in ichunks:
            arr = hf[chunk][:]
            for value in arr:
                ichunks_data.append(value)

        for chunk in qchunks:
            arr = hf[chunk][:]
            for value in arr:
                qchunks_data.append(value)

    # viewing the first chunk only
    testlist_I = np.array(testlist_I)
    testlist_Q = np.array(testlist_Q)

    # data from all response chunks
    ichunks_data = np.array(ichunks_data)
    qchunks_data = np.array(qchunks_data)

    # Making a single complex array
    IQ_test = testlist_I + 1j * testlist_Q
    IQ_scaled = ichunks_data + 1j * qchunks_data

    # Getting power and voltage
    power = np.abs(IQ_scaled) ** 2
    voltage = np.abs(IQ_scaled)
    phase = np.angle(IQ_scaled)
    t = np.arange(len(power))
    print("Max power is: " + str(max(power)))

    return power, phase, t

def main():
    global antenna_list
    global pulse_list
    global timing_list
    global delete_element_list
    global root_list
    global fig, ax
    global fersxml_results
    global globalprf
    global prop_speed
    global wsl_shared_directory
    global h5_results

    # Creating directory for shared files between Windows and WSL
    #if not os.path.exists(wsl_shared_directory):
     #   os.makedirs(wsl_shared_directory)

    # Basic UI Definitions
    tree = ""
    master = tk.Tk()


    #main container
    main_frame = ttk.Frame(master)
    main_frame.pack(fill='both', expand=True)

    master.title("FERS GUI")
    #master.geometry("1000x1080")


    # ATTEMPT AT MAKING SOME NICE TABS

    container = ttk.Notebook(main_frame)
    container.pack(fill='both', expand=True)

    tab1 = ttk.Frame(container)
    tab2 = ttk.Frame(container)
    tab3 = ttk.Frame(container)
    container.add(tab1, text='Parameters')
    container.add(tab2, text='Platforms')
    container.add(tab3, text='Plots')

    tab1.columnconfigure(2, minsize=20)
    tab2.columnconfigure(2, minsize=20)
    tab3.columnconfigure(2, minsize=20)

    # constants
    c = 330  # m/sec
    root_list = tk.Listbox(tab2, selectmode=tk.SINGLE)
    root_list.grid(row=15, column=6, rowspan=6)
    name_label = add_label(tab1, "Simulation Name", 1,0)
    name_entry = add_entry(tab1, 1, 1)

    # Basic Parameters
    starttime_label = add_label(tab1,"Start Time (s)", 2,0)
    starttime_entry = add_entry(tab1, 2,1)
    endtime_label = add_label(tab1,"End Time (s)", 3,0)
    endtime_entry = add_entry(tab1, 3,1)
    c_label = add_label(tab1,"Propagation Speed (m/s)", 4,0)
    c_entry = add_entry(tab1, 4, 1)
    rate_label = add_label(tab1, "Rate (Hz)", 5, 0)
    rate_entry = add_entry(tab1, 5, 1)

    # Export option
    export_xml = tk.StringVar()
    export_csv = tk.StringVar()
    export_binary = tk.StringVar()
    export_csvBinary = tk.StringVar()

    ttk.Checkbutton(tab1, text='Export xml', variable=export_xml).grid(row=6, column=1, sticky="w")
    ttk.Checkbutton(tab1, text='Export csv', variable=export_csv).grid(row=7, column=1, sticky="w")
    ttk.Checkbutton(tab1, text='Export binary', variable=export_binary).grid(row=8, column=1, sticky="w")
    ttk.Checkbutton(tab1, text='Export csvbinary', variable=export_csvBinary).grid(row=9, column=1, sticky="w")

    # Pulse entries
    add_label(tab1, "Pulse:", 12,0, "header")
    pulsename_label =add_label(tab1, "Pulse Name",13,0)
    pulsename_entry = add_entry(tab1, 13,1)
    pulsefile_label = add_label(tab1, "Filename (Full path)", 14,0)
    pulsefile_entry = add_entry(tab1, 14,1)
    pulsepower_label = add_label(tab1, "Power (W)",15,0)
    pulsepower_entry = add_entry(tab1, 15,1)
    pulsecarrier_label = add_label(tab1, "Carrier (Hz)",16,0)
    pulsecarrier_entry = add_entry(tab1, 16,1)

    add_label(tab1, "Timing:", 19,0, "header")
    timing_label = add_label(tab1, "Timing Name", 20,0)
    timing_entry = add_entry(tab1, 20,1)
    freq_label = add_label(tab1, "Frequency (Hz)", 21,0)
    freq_entry = add_entry(tab1, 21,1)
    jitter_label = add_label(tab1, "Jitter (Hz)", 22,0)
    jitter_entry = add_entry(tab1, 22,1)

    add_label(tab1, "Antenna:", 25,0, "header")
    ant_label = add_label(tab1, "antenna name", 26,0)
    ant_name = add_entry(tab1, 26,1)
    ant_pattern = add_label(tab1, "Antenna pattern", 27,0)
    pattern_entry = add_entry(tab1, 27,1)

    # Entry blocks for file destinations
    '''
    add_label(tab1, "Directories:", 1,3, "header")
    add_label(tab1, "Input (FERSXML) file destination: ", 2,3)
    input_file_entry = add_entry(tab1, 2, 4)
    add_label(tab1, "WSL Home Directory (/home/user...): ", 3,3)
    wsl_home_entry = add_entry(tab1, 3, 4)
    '''
    #Flexible Extensible Radar System Label

    tk.Label(tab1, text="Flexible Extensible Radar System",font=("Times New Roman", 20)).grid(row=0, column=0, columnspan=8, sticky='w')


    #PLATFORM
    platformname_label = add_label(tab2, "Platform Name", 0, 3, 'header')
    platformname_entry = add_entry(tab2, 0, 4)
    mpi_label = add_label(tab2, "Motionpath Interpolation", 1,3)
    #mpi_entry = add_entry(master, 1,4)
    choice1 = StringVar(tab2)
    choice1.set("static")
    w = OptionMenu(tab2, choice1, "static", "linear", "cubic")
    w.grid(row=1,column=4, sticky="w")
    x_label = add_label(tab2, "X (m)", 2,3)
    x_entry = add_entry(tab2, 2,4)
    y_label = add_label(tab2, "Y (m)", 3,3)
    y_entry = add_entry(tab2, 3,4)
    alt_label = add_label(tab2, "Altitude (m)", 4,3)
    alt_entry = add_entry(tab2, 4,4)
    time_label = add_label(tab2, "Time (s)", 5,3)
    time_entry = add_entry(tab2, 5,4)

    platform_rotation = StringVar(tab2)
    platform_rotation.set("fixedrotation")
    pr_options = OptionMenu(tab2, platform_rotation, "rotationpath", "fixedrotaion")
    pr_options.grid(row=7, column=4, sticky="w")
    choose_rotation_label = add_label(tab2, "Choose rotation", 7,3)

    #fixed rotation parameters
    fixed_rotation_label = add_label(tab2, "Fixed Rotation Parameters", 8,3, 'header')
    start_azimuth_label = add_label(tab2, "Start Azimuth", 9,3)
    start_azimuth_entry = add_entry(tab2, 9,4)
    start_elevation_label = add_label(tab2, "Start elevation", 10,3)
    start_elevation_entry = add_entry(tab2, 10,4)
    azimuth_rate_label = add_label(tab2, "Azimuth rate", 11,3)
    azimuth_rate_entry = add_entry(tab2, 11,4)
    ele_rate_label = add_label(tab2, "Elevation rate", 12,3)
    ele_rate_entry = add_entry(tab2, 12,4)

    #rotation path parameters
    rotatiopath_label = add_label(tab2, "Rotationpath parameters", 13,3, 'header')
    LorC_option = StringVar(tab2)
    LorC_option.set("linear")
    lorc_optionmenu = OptionMenu(tab2, LorC_option, "linear", "cubic")
    lorc_optionmenu.grid(row=14,column=4, sticky="w")
    lorc_label = add_label(tab2, "Rotationpath Interpolation", 14,3)
    azimuth_label = add_label(tab2, "Azimuth", 15, 3)
    azimuth_entry = add_entry(tab2, 15, 4)
    ele_label = add_label(tab2, "Elevation", 16, 3)
    ele_entry = add_entry(tab2, 16, 4)

    #monostatic parameters
    monostatic_label = add_label(tab2, "Monostatic Parameters", 17,3, 'header')
    mono_name_label = add_label(tab2, "Name", 18,3)
    mono_name_entry = add_entry(tab2, 18,4)
    mono_type = StringVar(tab2)
    mono_type.set("pulsed")
    mono_type_optionmenu = OptionMenu(tab2, mono_type, "pulsed", "continuous")
    mono_type_optionmenu.grid(row=19,column=4, sticky="w")
    mono_type_label = add_label(tab2, "Monostatic Type", 19,3)
    mono_antenna_label = add_label(tab2, "Antenna", 9,5)
    mono_antenna = StringVar(tab2)
    mono_antenna.set("Choose antenna")
    antenna_list.append("<select from below>")
    mono_antenna_om = OptionMenu(tab2, mono_antenna, *antenna_list)
    mono_antenna_om.grid(row=15,column=5, sticky="w")


    mono_pulse_label = add_label(tab2, "Pulse", 10, 5)
    mono_pulse = StringVar(tab2)
    mono_pulse.set("Choose pulse")
    pulse_list.append("<select from below>")
    mono_pulse_om = OptionMenu(tab2, mono_pulse, *pulse_list)
    mono_pulse_om.grid(row=14, column=5, sticky="w")

    #mono_timing_label = add_label(tab2, "Timing", 11, 5)
    mono_timing = StringVar(tab2)
    mono_timing.set("Choose timing")
    timing_list.append("<select from below>")
    mono_timing_om = OptionMenu(tab2, mono_timing, *timing_list)
    mono_timing_om.grid(row=16, column=5, sticky="w")
    prf_label = add_label(tab2, "PRF", 20,3)
    prf_entry = add_entry(tab2, 20,4)
    noise_temp_label = add_label(tab2, "Noise temp", 21,3)
    noise_temp_entry = add_entry(tab2, 21,4)
    mono_window_skip_label = add_label(tab2, "Window Skip (s)", 22,3)
    mono_window_skip_entry = add_entry(tab2, 22,4)
    mono_window_len_label = add_label(tab2, "Window Length (s)", 23,3)
    mono_window_len_entry = add_entry(tab2, 23,4)

    # TRANSMITTER PARAMETERS
    tranmitter_label = add_label(tab2, "Transmitter Parameters", 0,5, 'header')
    trans_name_label = add_label(tab2, "Transmitter Name", 1,5)
    trans_name_entry = add_entry(tab2, 1,6)
    trans_prf_label = add_label(tab2, "PRF", 2,5)
    trans_prf_entry = add_entry(tab2, 2,6)
    trans_type_label = add_label(tab2, "Transmitter Type", 3,5)
    trans_type = StringVar(tab2)
    trans_type.set("pulsed")
    trans_type_om = OptionMenu(tab2, trans_type, "pulsed", "continuous")
    trans_type_om.grid(row=3,column=6)
    # RECEIVER PARAMETERS
    receiver_label = add_label(tab2, "Receiver Parameters", 4,5, 'header')
    receiver_name_label = add_label(tab2, "Receiver Name", 5,5)
    receiver_name_entry = add_entry(tab2, 5,6)
    window_skip_label = add_label(tab2, "Window Skip (s)", 6,5)
    window_skip_entry = add_entry(tab2, 6,6)
    window_len_label = add_label(tab2, "Window Length (s)", 7,5)
    window_len_entry = add_entry(tab2, 7,6)

    #TARGET PARAMETERS
    target_label = add_label(tab2, "Target Parameters", 8,5, 'header')
    target_name_label = add_label(tab2, "Target Name", 9,5)
    target_name_entry = add_entry(tab2, 9,6)
    rcs_type_label = add_label(tab2, "RCS Type", 10,5)
    rcs_type_entry = add_entry(tab2, 10,6)
    value_label = add_label(tab2, "Value", 11,5)
    value_entry = add_entry(tab2, 11,6)

    # Selecting Antennas, Pulses, and Timings
    apt_selection = add_label(tab2, "Choose Antenna/Pulse/Timing", 12, 5, 'header')

    # Deleting elements:
    delete_element_label = add_label(tab2, "Remove Element (Current Session)", 13,5)
    delete_element = StringVar(tab2)
    delete_element.set("<Choose element>")
    delete_element_list.append("...")
    delete_menu = OptionMenu(tab2, delete_element, *delete_element_list)
    delete_menu.grid(row=13, column=6)
    delete_menu.config(width=15)

    #check to see if file has been loaded in
    #load_check = check_root_list(root_list)


    def add_parameters():
        global tree
        global prop_speed
        global delete_element_list
        global root_elements
        global root_list
        global dummy
        load_check = check_root_list(root_list)

        # Get parameters
        name = name_entry.get()
        starttime = starttime_entry.get()
        endtime = endtime_entry.get()
        c = c_entry.get()
        prop_speed = c_entry.get()
        rate = rate_entry.get()
        delete_element_list.append(name)

        # Get export selections
        xml = export_xml.get()
        csv = export_csv.get()
        binary = export_binary.get()
        csvbinary = export_csvBinary.get()
        # create xml
        tree = make_tree(name)
        dummy = name
        print(tree)
        print(name)

        if load_check == False:
            parameters = create_xml(tree.getroot(), starttime, endtime, c, rate, xml, csv, binary, csvbinary)
            print(parameters)
            print(xml)
            print(binary)
            # add to list of removable elements
            delete_menu = OptionMenu(tab2, delete_element, *delete_element_list)
            delete_menu.grid(row=13, column=6)
            delete_menu.config(width=15)

        if load_check == True:
            parameters = create_xml(load_tree.getroot(), starttime, endtime, c, rate, xml, csv, binary, csvbinary)
            root_elements.append(parameters)
            root_list.insert(tk.END, name)
        print("parameters added")


    def add_pulse():
        global tree
        global pulse_list
        global mono_pulse_om
        global delete_element_list
        global root_elements
        global root_list
        load_check = check_root_list(root_list)
        pulsename = pulsename_entry.get()
        pulsefile = pulsefile_entry.get()
        pulsefile_path = '/mnt/c/Users/samja/wsl_share/' + str(pulsefile)
        #shutil.copy(pulsefile, 'C:/Users/samja/wsl_share')
        pulsepower = pulsepower_entry.get()
        pulsecarrier = pulsecarrier_entry.get()
        pulse_list.append(pulsename)
        delete_element_list.append(pulsename)

        if load_check == False:
            print("No detected xml file")
            pulse = make_pulse_element(tree.getroot(), pulsename, pulsefile_path, pulsepower, pulsecarrier)
            print(pulse)

            #making currently added pulses available
            mono_pulse_om = OptionMenu(tab2, mono_pulse, *pulse_list)
            mono_pulse_om.grid(row=14, column=5, sticky="w")

            #add to list of removable elements
            delete_menu = OptionMenu(tab2, delete_element, *delete_element_list)
            delete_menu.grid(row=13, column=6)
            delete_menu.config(width=15)

        #adding pulse to an xml that has been loaded in

        if load_check == True:
            pulse = make_pulse_element(load_tree.getroot(), pulsename, pulsefile, pulsepower, pulsecarrier)
            root_elements.append(pulse)
            root_list.insert(tk.END, pulsename)
            print(pulse)

        #function for clearing entries after the element is added
        clear_entry(pulsename_entry, pulsepower_entry, pulsecarrier_entry)
        print("pulse %s added" % pulsename)
        print("pulse list: " + str(pulse_list))
    def add_timing():
        global tree
        global timing_list
        global delete_element_list
        global root_elements
        global root_list
        load_check = check_root_list(root_list)
        print(load_check)
        timingname = timing_entry.get()
        freqentry = freq_entry.get()
        jitterentry = jitter_entry.get()
        timing_list.append(timingname)
        delete_element_list.append(timingname)

        #If a file was NOT loaded in (building a file)
        if load_check == False:

            timing = timing_source(tree.getroot(), timingname, freqentry, jitterentry)
            print(timing)
            mono_timing_om = OptionMenu(tab2, mono_timing, *timing_list)
            mono_timing_om.grid(row=16, column=5, sticky="w")

            # add to list of removable elements
            delete_menu = OptionMenu(tab2, delete_element, *delete_element_list)
            delete_menu.grid(row=13, column=6)
            delete_menu.config(width=15)

        #If a file was loaded in
        if load_check == True:
            timing = timing_source(load_tree.getroot(), timingname, freqentry, jitterentry)
            root_elements.append(timing)
            root_list.insert(tk.END, timingname)
            print(timing)

        clear_entry(timing_entry, freq_entry, jitter_entry)
        print("timing %s added"%timingname)
    def add_antenna():
        global tree
        global antenna_list
        global delete_element_list
        global root_elements
        global root_list

        load_check = check_root_list(root_list)

        antenna_pattern = pattern_entry.get()
        antenna_name = ant_name.get()
        antenna_list.append(antenna_name)
        delete_element_list.append(antenna_name)

        if load_check == False:
            antenna = make_antenna(tree.getroot(), antenna_name, antenna_pattern)
            print(antenna)

            mono_antenna_om = OptionMenu(tab2, mono_antenna, *antenna_list)
            mono_antenna_om.grid(row=15, column=5, sticky="w")

            # add to list of removable elements
            delete_menu = OptionMenu(tab2, delete_element, *delete_element_list)
            delete_menu.grid(row=13, column=6)
            delete_menu.config(width=15)

        if load_check == True:
            antenna = make_antenna(load_tree.getroot(), antenna_name, antenna_pattern)
            root_elements.append(antenna)
            root_list.insert(tk.END, antenna_name)

        clear_entry(pattern_entry, ant_name)
        print("antenna %s added" % antenna_name)
    def add_platform():
        global tree
        global antenna_list
        global delete_element_list
        global globalprf
        global root_elements
        global root_list

        load_check = check_root_list(root_list)

        platformname = platformname_entry.get()
        mchoose = choice1.get()

        # Position waypoint
        x = x_entry.get()
        y = y_entry.get()
        altitude = alt_entry.get()
        motiontime = time_entry.get()
        delete_element_list.append(platformname)

        #FIXED ROTATION PARAMETERS
        startazimuth = start_azimuth_entry.get()
        startelevation = start_elevation_entry.get()
        azimuthrate = azimuth_rate_entry.get()
        elevationrate = ele_rate_entry.get()

        rotation_type = platform_rotation.get()

        #ROTATION PATH PARAMETERS
        lORc = LorC_option.get()
        azimuth = azimuth_entry.get()
        elevation = ele_entry.get()

        #MONOSTATIC PARAMETERS
        mononame = mono_name_entry.get()
        monotype = mono_type.get()
        antenna = mono_antenna.get()
        pulse = mono_pulse.get()
        timing = mono_timing.get()
        monoprf = prf_entry.get()
        globalprf = prf_entry.get()
        noisetemp = noise_temp_entry.get()
        mono_win_skip = mono_window_skip_entry.get()
        mono_win_len = mono_window_len_entry.get()
        delete_element_list.append(mononame)

        #TRANSMITTER
        transprf = trans_prf_entry.get()
        transname = trans_name_entry.get()
        globalprf = trans_prf_entry.get()
        transtype = trans_type.get()
        delete_element_list.append(transname)

        #receiver
        receivername = receiver_name_entry.get()
        winskip = window_skip_entry.get()
        winlen = window_len_entry.get()
        delete_element_list.append(receivername)

        #target
        targetname = target_name_entry.get()
        rcstype = rcs_type_entry.get()
        value = value_entry.get()
        delete_element_list.append(targetname)

        if load_check == False:
            platform = make_platform(tree.getroot(), platformname, mchoose, x, y, altitude, motiontime)

            if rotation_type == "fixedrotation":
                make_fixed_rotation(plat_element, startazimuth, startelevation, azimuthrate, elevationrate)

            elif rotation_type == "rotationpath":
                make_rotation_path(plat_element, lORc, azimuth, elevation)
            #fixed rotation by default
            else:
                make_fixed_rotation(plat_element, startazimuth, startelevation, azimuthrate, elevationrate)


            if len(mononame) != 0:
                make_monostatic(plat_element, mononame, monotype, antenna, pulse, timing, monoprf, noisetemp, mono_win_skip, mono_win_len)
            if len(transname) != 0:
                make_transmitter(plat_element, transname, transprf, transtype, pulse, antenna, timing)
            if len(receivername) != 0:
                make_receiver(plat_element, receivername, antenna, timing, winskip, winlen)
            if len(targetname) != 0:
                make_target(plat_element, targetname, value, rcstype)

            # add to list of removable elements
            delete_menu = OptionMenu(tab2, delete_element, *delete_element_list)
            delete_menu.grid(row=13, column=6)
            delete_menu.config(width=15)
            print("platform added")

        if load_check == True:
            platform = make_platform(load_tree.getroot(), platformname, mchoose, x, y, altitude, motiontime)
            root_elements.append(platform)
            root_list.insert(tk.END, platformname)
            print(pulse)

            if rotation_type == "fixedrotation":
                make_fixed_rotation(plat_element, startazimuth, startelevation, azimuthrate, elevationrate)

            elif rotation_type == "rotationpath":
                make_rotation_path(plat_element, lORc, azimuth, elevation)
            # fixed rotation by default
            else:
                make_fixed_rotation(plat_element, startazimuth, startelevation, azimuthrate, elevationrate)

            if len(mononame) != 0:
                make_monostatic(plat_element, mononame, monotype, antenna, pulse, timing, monoprf, noisetemp,
                                mono_win_skip, mono_win_len)
            if len(transname) != 0:
                make_transmitter(plat_element, transname, transprf, transtype, pulse, antenna, timing)
            if len(receivername) != 0:
                make_receiver(plat_element, receivername, antenna, timing, winskip, winlen)
            if len(targetname) != 0:
                make_target(plat_element, targetname, value, rcstype)

             # add to list of removable elements
            delete_menu = OptionMenu(tab2, delete_element, *delete_element_list)
            delete_menu.grid(row=13, column=6)
            delete_menu.config(width=15)
            print("platform added succc sexfully")


        #MAKING ADDITIONAL THINGS
    def add_pos_waypoint():
        # Position waypoint
        x = x_entry.get()
        y = y_entry.get()
        altitude = alt_entry.get()
        motiontime = time_entry.get()
        make_position_element(x, y, altitude, motiontime)
        print("Additional position waypoint added")

    def remove_element(element):
        global tree
        main_root = tree.getroot()
        remove_ele = main_root.find(element)
        if remove_ele is not None:
            main_root.remove(remove_ele)

    def delete_element_button():
        global delete_element_list
        item = delete_element.get()
        remove_element(item)
        delete_element_list.remove(item)
        delete_menu = OptionMenu(tab2, delete_element, *delete_element_list)
        delete_menu.config(width=15)
        delete_menu.grid(row=13, column=6)
        delete_element.set("...")

    def save_data():
        global tree
        #C:\Users\samja\PycharmProjects\final\venv
        file_path = 'C:/Users/' + str(name_entry.get())+'.fersxml'
        file_path2 = str(name_entry.get()) + ".xml"
        save_xml2(tree, file_path, file_path2)

        print("data saved flawlessly :)")

    # Diplaying plots on the GUI

    fig, ax = plt.subplots()
    canvas = FigureCanvasTkAgg(fig, master=tab3)
    canvas.get_tk_widget().configure(width=200, height=200)
    canvas.get_tk_widget().pack(side=BOTTOM, fill='both', expand=True)

    #making a frame for the label representing current file
    r_label = ttk.Label(master=tab3, text="No file selected")
    r_label.pack(side=BOTTOM, anchor="w")
    def load_results_xml():
        global fersxml_results
        #plot_label_frame = ttk.Frame(tab3).pack(side=BOTTOM, anchor='w')
        fp = filedialog.askopenfilename(filetypes=[("XML files", "*.fersxml")])

        if not fp:
            return
        #fp = os.path.basename(fp)
        fersxml_results = str(fp)
        print(fersxml_results)
        r_label.config(text=fersxml_results)

    def load_h5_results():
        global h5_results
        fp = filedialog.askopenfilename(filetypes=[("HDF5 files", "*.h5")])
        if not fp:
            return

        h5_results = str(fp)
        r_label.config(text=h5_results)


    def show_plot(type):
        print("prop speed: " + str(get_c()))
        print("PRF is: " + str(get_prf()))

        if fersxml_results != "":
            time, power, doppler, range, phase, phasedeg, amp, num_targets = plot_XvT(fersxml_results, get_c(), get_prf())

        if h5_results != "":
            h5power, h5phase, h5time = read_h5(h5_results)


        if type == "power":
            r_label.config(text=fersxml_results)
            ax.clear()
            #ax.plot(time, power, "-o", color='black', markersize=0, linewidth=0.5)
            ax.scatter(time, power, label="PvT", color='blue', s=20)
            ax.set_title("Power vs time")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Power (W)")
            ax.grid(True)
            canvas.draw()

        if type == "doppler":
            r_label.config(text=fersxml_results)
            ax.clear()
            #ax.plot(time, doppler, "-o", color='black', markersize=0, linewidth=0.5)
            ax.scatter(time, doppler, label="PvT", color='blue', s=20)
            ax.set_title("Doppler vs time")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Doppler (Hz)")
            ax.grid(True)
            canvas.draw()

        if type == "phase":
            r_label.config(text=fersxml_results)
            ax.clear()
            #ax.plot(time, phase, "-o", color='black', markersize=0, linewidth=0.5)
            ax.scatter(time, phase, label="PvT", color='blue', s=20)
            ax.set_title("Phase vs Time")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Phase")
            ax.grid(True)
            canvas.draw()

        if type == "phasedeg":
            r_label.config(text=fersxml_results)
            ax.clear()
            #ax.plot(time, phasedeg, "-o", color='black', markersize=0, linewidth=0.5)
            ax.scatter(time, phasedeg, label="PvT", color='blue', s=20)
            ax.set_title("phasedeg vs time")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("phase degree")
            ax.grid(True)
            canvas.draw()

        if type == "amp":
            r_label.config(text=fersxml_results)
            ax.clear()
            #ax.plot(time, amp, "-o", color='black', markersize=0, linewidth=0.5)
            ax.scatter(time, amp, label="PvT", color='blue', s=20)
            ax.set_title("Amplitude vs Time")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            ax.grid(True)
            canvas.draw()

        if type == "range":
            if get_prf() > 0:
                ax.clear()
                ax.plot(range, power, "+")
                ax.set_title("Doppler vs time")
                ax.set_xlabel("Range (m)")
                ax.set_ylabel("Power")
                ax.grid(True)
                canvas.draw()
            else:
                print("PRF is 0. Please load a file")

        if type == "h5power":
            ax.clear()
            ax.plot(h5time, h5power)
            #ax.plot(h5time, h5power, "-o", color='black', markersize=0, linewidth=0.5)
            #ax.scatter(h5time, h5power, label="PvT", color='blue', s=20)
            ax.set_title("Power vs time")
            ax.set_xlabel("Samples")
            ax.set_ylabel("Power (W)")
            ax.grid(True)
            canvas.draw()

    # buttons
    tk.Button(tab2, text='Quit', width=13, command=master.quit).grid(row=25, column=3, sticky=tk.W,pady=4)
    #tk.Button(tab1, text='Write data', command=write_data).grid(row=40, column=1, sticky=tk.W, pady=4)
    tk.Button(tab1, text='add parameters', command=add_parameters).grid(row=10, column=1, sticky=tk.W, pady=4)
    tk.Button(tab1, text='add pulse', command=add_pulse).grid(row=17, column=1, sticky=tk.W, pady=4)
    tk.Button(tab1, text='add timing', command=add_timing).grid(row=23, column=1, sticky=tk.W, pady=4)
    tk.Button(tab1, text='add antenna', command=add_antenna).grid(row=28, column=1, sticky=tk.W, pady=4)


    tk.Button(tab2, text='Run Simulation', height=3, width=13 ,command=run_sim).grid(row=21, column=5, sticky=tk.W, pady=4, rowspan=5)
    tk.Button(tab2, text='Add platform', width=13, command=add_platform).grid(row=25, column=4, sticky=tk.W,pady=4)
    tk.Button(tab2, text='Write xml', width=13, command=save_data).grid(row=25, column=5,sticky=tk.W, pady=4)
    tk.Button(tab2, text='Delete', width=13, command=delete_element_button).grid(row=14, column=6, sticky=tk.W, pady=4)
    tk.Button(tab2, text='Load XML', width=13, command=load_xml).grid(row=21, column=6, pady=4)
    tk.Button(tab2, text='Delete root', width=13, command=remove_root).grid(row=22, column=6, pady=4)
    tk.Button(tab2, text='Write Loaded XML', width=13, command=write_loaded_xml).grid(row=23, column=6, pady=4)
    tk.Button(tab2, text='Add positionwaypoint', command=add_pos_waypoint).grid(row=6, column=3, sticky=tk.W, pady=4)

    # Button Frame for plot buttons
    plot_buttons = ttk.Frame(tab3)
    plot_buttons.pack(side=TOP, anchor='w')
    tk.Button(plot_buttons, text="Power vs Time", command=lambda: show_plot("power")).pack(side=LEFT)
    tk.Button(plot_buttons, text="Doppler vs Time", command=lambda: show_plot("doppler")).pack(side=RIGHT)
    #tk.Button(plot_buttons, text="Power vs Range", command=lambda: show_plot("range")).pack(side=RIGHT)
    tk.Button(plot_buttons, text="Phase vs Time", command=lambda: show_plot("phase")).pack(side=RIGHT)
    tk.Button(plot_buttons, text="Phase Deg vs Time", command=lambda: show_plot("phasedeg")).pack(side=RIGHT)
    tk.Button(plot_buttons, text="Amplitude vs Time", command=lambda: show_plot("amp")).pack(side=RIGHT)
    tk.Button(plot_buttons, text="H5 Power vs Time", command=lambda: show_plot("h5power")).pack(side=RIGHT)


    add_plot_buttons = ttk.Frame(tab3)
    add_plot_buttons.pack(side=BOTTOM, anchor='w')
    tk.Button(add_plot_buttons, text="Load results file", command=load_results_xml).pack(side=LEFT)
    tk.Button(add_plot_buttons, text="Load HDF5 file", command=load_h5_results).pack(side=LEFT)
    tk.Button(add_plot_buttons, text="Quit", command=master.quit).pack(side=RIGHT)


    tk.mainloop()

    print("Entry count = " + str(entry_count))
    # print(test())
    print("...GUI script finalised")


if __name__ == "__main__":
    main()