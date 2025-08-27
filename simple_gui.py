#!/usr/bin/env python3
"""
Simple Tkinter GUI for Testing Raspberry Pi Feed Control System
Updated to use centralized configuration from config.py with config editor
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import json
import ast
from datetime import datetime

from main import FeedControlSystem

# Import configuration
from config import (
    get_available_pumps, get_available_relays, get_available_flow_meters,
    get_pump_name, get_relay_name, get_flow_meter_name,
    PUMP_NAMES, RELAY_NAMES, FLOW_METER_NAMES,
    MIN_PUMP_VOLUME_ML, MAX_PUMP_VOLUME_ML,
    MAX_FLOW_GALLONS, MOCK_SETTINGS,
    EC_CALIBRATION_SOLUTIONS, PH_CALIBRATION_SOLUTIONS
)
import config

class FeedControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Raspberry Pi Feed Control System - Test GUI (Using Config)")
        self.root.geometry("1400x900")
        
        # Initialize system
        self.system = None
        self.system_running = False
        
        # Configuration editor variables
        self.config_vars = {}
        self.config_changed = False
        
        # Create GUI elements with tabs
        self.create_tabbed_interface()
        
        # Schedule system start after main loop begins
        self.root.after(100, self.start_system)
        
        # Schedule status updates after main loop begins
        self.root.after(500, self.update_status)
    
    def create_tabbed_interface(self):
        """Create tabbed interface with main controls and config editor"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main control tab
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="System Control")
        
        # Configuration editor tab
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Configuration Editor")
        
        # Create main control widgets
        self.create_main_widgets(main_frame)
        
        # Create configuration editor
        self.create_config_editor(config_frame)
    
    def create_main_widgets(self, parent):
        """Create main control widgets in the main tab"""
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)
        
        # System status frame
        self.create_status_frame(parent)
        
        # Control frames
        self.create_control_frames(parent)
        
        # Log frame
        self.create_log_frame(parent)
    
    def create_config_editor(self, parent):
        """Create configuration editor interface"""
        # Main container with scrolling
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Header
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="System Configuration Editor", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Save/Reset buttons
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset to Current", command=self.reset_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Load from File", command=self.load_config_file).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.config_status_label = ttk.Label(header_frame, text="", foreground="green")
        self.config_status_label.pack(side=tk.RIGHT, padx=(20, 0))
        
        # Create config sections
        self.create_pump_config_section(scrollable_frame)
        self.create_relay_config_section(scrollable_frame)
        self.create_flow_config_section(scrollable_frame)
        self.create_arduino_config_section(scrollable_frame)
        self.create_system_config_section(scrollable_frame)
        self.create_mock_config_section(scrollable_frame)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load initial values
        self.load_current_config()
    
    def create_pump_config_section(self, parent):
        """Create pump configuration section"""
        frame = ttk.LabelFrame(parent, text="Pump Configuration", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        # Pump addresses and names
        ttk.Label(frame, text="Pump Addresses & Names:", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=4, sticky=tk.W)
        
        self.pump_entries = {}
        for i, pump_id in enumerate(sorted(get_available_pumps())):
            row = i + 1
            
            ttk.Label(frame, text=f"Pump {pump_id}:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5))
            
            # I2C Address
            ttk.Label(frame, text="I2C Addr:").grid(row=row, column=1, sticky=tk.W, padx=(10, 2))
            addr_var = tk.StringVar()
            addr_entry = ttk.Entry(frame, textvariable=addr_var, width=5)
            addr_entry.grid(row=row, column=2, sticky=tk.W, padx=(0, 10))
            
            # Name
            ttk.Label(frame, text="Name:").grid(row=row, column=3, sticky=tk.W, padx=(10, 2))
            name_var = tk.StringVar()
            name_entry = ttk.Entry(frame, textvariable=name_var, width=20)
            name_entry.grid(row=row, column=4, sticky=tk.W)
            
            self.pump_entries[pump_id] = {'address': addr_var, 'name': name_var}
        
        # Volume limits
        limits_frame = ttk.Frame(frame)
        limits_frame.grid(row=len(self.pump_entries) + 2, column=0, columnspan=5, sticky=tk.W, pady=(10, 0))
        
        ttk.Label(limits_frame, text="Volume Limits:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Label(limits_frame, text="Min (ml):").pack(side=tk.LEFT, padx=(20, 2))
        
        self.min_pump_volume_var = tk.StringVar()
        ttk.Entry(limits_frame, textvariable=self.min_pump_volume_var, width=8).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(limits_frame, text="Max (ml):").pack(side=tk.LEFT, padx=(10, 2))
        self.max_pump_volume_var = tk.StringVar()
        ttk.Entry(limits_frame, textvariable=self.max_pump_volume_var, width=8).pack(side=tk.LEFT)
    
    def create_relay_config_section(self, parent):
        """Create relay configuration section"""
        frame = ttk.LabelFrame(parent, text="Relay Configuration", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="Relay GPIO Pins & Names:", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=4, sticky=tk.W)
        
        self.relay_entries = {}
        available_relays = get_available_relays()
        
        for i, relay_id in enumerate(sorted(available_relays)):
            row = i + 1
            
            ttk.Label(frame, text=f"Relay {relay_id}:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5))
            
            # GPIO Pin
            ttk.Label(frame, text="GPIO Pin:").grid(row=row, column=1, sticky=tk.W, padx=(10, 2))
            gpio_var = tk.StringVar()
            gpio_entry = ttk.Entry(frame, textvariable=gpio_var, width=5)
            gpio_entry.grid(row=row, column=2, sticky=tk.W, padx=(0, 10))
            
            # Name
            ttk.Label(frame, text="Name:").grid(row=row, column=3, sticky=tk.W, padx=(10, 2))
            name_var = tk.StringVar()
            name_entry = ttk.Entry(frame, textvariable=name_var, width=25)
            name_entry.grid(row=row, column=4, sticky=tk.W)
            
            self.relay_entries[relay_id] = {'gpio': gpio_var, 'name': name_var}
        
        # Relay logic setting
        logic_frame = ttk.Frame(frame)
        logic_frame.grid(row=len(self.relay_entries) + 2, column=0, columnspan=5, sticky=tk.W, pady=(10, 0))
        
        ttk.Label(logic_frame, text="Relay Logic:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.relay_active_high_var = tk.BooleanVar()
        ttk.Checkbutton(logic_frame, text="Active HIGH (GPIO HIGH = Relay ON)", 
                       variable=self.relay_active_high_var).pack(side=tk.LEFT, padx=(10, 0))
    
    def create_flow_config_section(self, parent):
        """Create flow meter configuration section"""
        frame = ttk.LabelFrame(parent, text="Flow Meter Configuration", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="Flow Meter GPIO Pins & Names:", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=6, sticky=tk.W)
        
        self.flow_entries = {}
        for i, meter_id in enumerate(sorted(get_available_flow_meters())):
            row = i + 1
            
            ttk.Label(frame, text=f"Flow {meter_id}:").grid(row=row, column=0, sticky=tk.W, padx=(0, 5))
            
            # GPIO Pin
            ttk.Label(frame, text="GPIO Pin:").grid(row=row, column=1, sticky=tk.W, padx=(10, 2))
            gpio_var = tk.StringVar()
            gpio_entry = ttk.Entry(frame, textvariable=gpio_var, width=5)
            gpio_entry.grid(row=row, column=2, sticky=tk.W, padx=(0, 10))
            
            # Calibration
            ttk.Label(frame, text="PPG:").grid(row=row, column=3, sticky=tk.W, padx=(10, 2))
            cal_var = tk.StringVar()
            cal_entry = ttk.Entry(frame, textvariable=cal_var, width=8)
            cal_entry.grid(row=row, column=4, sticky=tk.W, padx=(0, 10))
            
            # Name
            ttk.Label(frame, text="Name:").grid(row=row, column=5, sticky=tk.W, padx=(10, 2))
            name_var = tk.StringVar()
            name_entry = ttk.Entry(frame, textvariable=name_var, width=20)
            name_entry.grid(row=row, column=6, sticky=tk.W)
            
            self.flow_entries[meter_id] = {'gpio': gpio_var, 'calibration': cal_var, 'name': name_var}
        
        # Flow limits
        limits_frame = ttk.Frame(frame)
        limits_frame.grid(row=len(self.flow_entries) + 2, column=0, columnspan=7, sticky=tk.W, pady=(10, 0))
        
        ttk.Label(limits_frame, text="Max Flow Gallons:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.max_flow_gallons_var = tk.StringVar()
        ttk.Entry(limits_frame, textvariable=self.max_flow_gallons_var, width=8).pack(side=tk.LEFT, padx=(10, 0))
    
    def create_arduino_config_section(self, parent):
        """Create Arduino configuration section"""
        frame = ttk.LabelFrame(parent, text="Arduino/EC-pH Configuration", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        # Serial ports
        ttk.Label(frame, text="Serial Ports (comma-separated):", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.arduino_ports_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.arduino_ports_var, width=50).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Baudrate
        ttk.Label(frame, text="Baudrate:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.arduino_baudrate_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.arduino_baudrate_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # EC Calibration Solutions
        ec_frame = ttk.Frame(frame)
        ec_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(15, 5))
        
        ttk.Label(ec_frame, text="EC Calibration Solutions:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        self.ec_cal_entries = {}
        ec_solutions = ['dry', 'single', 'low', 'high']
        for i, cal_type in enumerate(ec_solutions):
            solution_frame = ttk.Frame(ec_frame)
            solution_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(solution_frame, text=f"{cal_type.title()}:", width=8).pack(side=tk.LEFT)
            var = tk.StringVar()
            ttk.Entry(solution_frame, textvariable=var, width=10).pack(side=tk.LEFT, padx=(5, 0))
            self.ec_cal_entries[cal_type] = var
        
        # pH Calibration Solutions
        ph_frame = ttk.Frame(frame)
        ph_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        ttk.Label(ph_frame, text="pH Calibration Solutions:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        self.ph_cal_entries = {}
        ph_solutions = ['low', 'mid', 'high']
        for i, cal_type in enumerate(ph_solutions):
            solution_frame = ttk.Frame(ph_frame)
            solution_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(solution_frame, text=f"{cal_type.title()}:", width=8).pack(side=tk.LEFT)
            var = tk.StringVar()
            ttk.Entry(solution_frame, textvariable=var, width=10).pack(side=tk.LEFT, padx=(5, 0))
            self.ph_cal_entries[cal_type] = var
    
    def create_system_config_section(self, parent):
        """Create system configuration section"""
        frame = ttk.LabelFrame(parent, text="System Settings", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        # I2C Bus
        ttk.Label(frame, text="I2C Bus Number:").grid(row=0, column=0, sticky=tk.W)
        self.i2c_bus_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.i2c_bus_var, width=5).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # EZO Command Delay
        ttk.Label(frame, text="EZO Command Delay (s):").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.ezo_delay_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ezo_delay_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # Status Update Interval
        ttk.Label(frame, text="Status Update Interval (s):").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.status_interval_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.status_interval_var, width=8).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
    
    def create_mock_config_section(self, parent):
        """Create mock hardware configuration section"""
        frame = ttk.LabelFrame(parent, text="Mock Hardware Settings", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="Enable Mock Hardware:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        mock_frame = ttk.Frame(frame)
        mock_frame.pack(fill=tk.X, pady=5)
        
        self.mock_vars = {}
        mock_components = ['pumps', 'relays', 'flow_meters', 'arduino']
        
        for i, component in enumerate(mock_components):
            var = tk.BooleanVar()
            ttk.Checkbutton(mock_frame, text=component.replace('_', ' ').title(), 
                           variable=var).grid(row=i//2, column=i%2, sticky=tk.W, padx=(0, 20), pady=2)
            self.mock_vars[component] = var
    
    def load_current_config(self):
        """Load current configuration values into the editor"""
        try:
            # Pump configuration
            for pump_id, entries in self.pump_entries.items():
                entries['address'].set(str(config.PUMP_ADDRESSES.get(pump_id, pump_id)))
                entries['name'].set(get_pump_name(pump_id))
            
            self.min_pump_volume_var.set(str(config.MIN_PUMP_VOLUME_ML))
            self.max_pump_volume_var.set(str(config.MAX_PUMP_VOLUME_ML))
            
            # Relay configuration
            for relay_id, entries in self.relay_entries.items():
                entries['gpio'].set(str(config.RELAY_GPIO_PINS.get(relay_id, "")))
                entries['name'].set(get_relay_name(relay_id))
            
            self.relay_active_high_var.set(config.RELAY_ACTIVE_HIGH)
            
            # Flow meter configuration
            for meter_id, entries in self.flow_entries.items():
                entries['gpio'].set(str(config.FLOW_METER_GPIO_PINS.get(meter_id, "")))
                entries['calibration'].set(str(config.FLOW_METER_CALIBRATION.get(meter_id, 220)))
                entries['name'].set(get_flow_meter_name(meter_id))
            
            self.max_flow_gallons_var.set(str(config.MAX_FLOW_GALLONS))
            
            # Arduino configuration
            self.arduino_ports_var.set(", ".join(config.ARDUINO_UNO_PORTS))
            self.arduino_baudrate_var.set(str(config.ARDUINO_UNO_BAUDRATE))
            
            # Calibration solutions
            for cal_type, var in self.ec_cal_entries.items():
                var.set(str(config.EC_CALIBRATION_SOLUTIONS.get(cal_type, "")))
            
            for cal_type, var in self.ph_cal_entries.items():
                var.set(str(config.PH_CALIBRATION_SOLUTIONS.get(cal_type, "")))
            
            # System settings
            self.i2c_bus_var.set(str(config.I2C_BUS_NUMBER))
            self.ezo_delay_var.set(str(config.EZO_COMMAND_DELAY))
            self.status_interval_var.set(str(config.STATUS_UPDATE_INTERVAL))
            
            # Mock settings
            for component, var in self.mock_vars.items():
                var.set(config.MOCK_SETTINGS.get(component, False))
                
            self.config_status_label.config(text="Configuration loaded", foreground="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def save_config(self):
        """Save configuration changes to config.py file"""
        try:
            # Read current config.py file
            with open('config.py', 'r') as f:
                config_content = f.read()
            
            # Create a backup
            with open('config.py.backup', 'w') as f:
                f.write(config_content)
            
            # Build new configuration values
            new_config = {}
            
            # Pump configuration
            pump_addresses = {}
            pump_names = {}
            for pump_id, entries in self.pump_entries.items():
                try:
                    addr = int(entries['address'].get())
                    pump_addresses[pump_id] = addr
                    pump_names[pump_id] = entries['name'].get().strip()
                except ValueError:
                    pass
            
            new_config['PUMP_ADDRESSES'] = pump_addresses
            new_config['PUMP_NAMES'] = pump_names
            new_config['MIN_PUMP_VOLUME_ML'] = float(self.min_pump_volume_var.get())
            new_config['MAX_PUMP_VOLUME_ML'] = float(self.max_pump_volume_var.get())
            
            # Relay configuration
            relay_gpio_pins = {}
            relay_names = {}
            for relay_id, entries in self.relay_entries.items():
                try:
                    gpio = int(entries['gpio'].get())
                    relay_gpio_pins[relay_id] = gpio
                    relay_names[relay_id] = entries['name'].get().strip()
                except ValueError:
                    pass
            
            new_config['RELAY_GPIO_PINS'] = relay_gpio_pins
            new_config['RELAY_NAMES'] = relay_names
            new_config['RELAY_ACTIVE_HIGH'] = self.relay_active_high_var.get()
            
            # Flow meter configuration
            flow_gpio_pins = {}
            flow_calibration = {}
            flow_names = {}
            for meter_id, entries in self.flow_entries.items():
                try:
                    gpio = int(entries['gpio'].get())
                    cal = int(entries['calibration'].get())
                    flow_gpio_pins[meter_id] = gpio
                    flow_calibration[meter_id] = cal
                    flow_names[meter_id] = entries['name'].get().strip()
                except ValueError:
                    pass
            
            new_config['FLOW_METER_GPIO_PINS'] = flow_gpio_pins
            new_config['FLOW_METER_CALIBRATION'] = flow_calibration
            new_config['FLOW_METER_NAMES'] = flow_names
            new_config['MAX_FLOW_GALLONS'] = int(self.max_flow_gallons_var.get())
            
            # Arduino configuration
            ports = [p.strip() for p in self.arduino_ports_var.get().split(',') if p.strip()]
            new_config['ARDUINO_UNO_PORTS'] = ports
            new_config['ARDUINO_UNO_BAUDRATE'] = int(self.arduino_baudrate_var.get())
            
            # Calibration solutions
            ec_cal = {}
            for cal_type, var in self.ec_cal_entries.items():
                val = var.get().strip()
                if val:
                    try:
                        ec_cal[cal_type] = int(val) if val.isdigit() else float(val) if val != "0" else 0
                    except:
                        pass
            new_config['EC_CALIBRATION_SOLUTIONS'] = ec_cal
            
            ph_cal = {}
            for cal_type, var in self.ph_cal_entries.items():
                val = var.get().strip()
                if val:
                    try:
                        ph_cal[cal_type] = float(val)
                    except:
                        pass
            new_config['PH_CALIBRATION_SOLUTIONS'] = ph_cal
            
            # System settings
            new_config['I2C_BUS_NUMBER'] = int(self.i2c_bus_var.get())
            new_config['EZO_COMMAND_DELAY'] = float(self.ezo_delay_var.get())
            new_config['STATUS_UPDATE_INTERVAL'] = float(self.status_interval_var.get())
            
            # Mock settings
            mock_settings = {}
            for component, var in self.mock_vars.items():
                mock_settings[component] = var.get()
            new_config['MOCK_SETTINGS'] = mock_settings
            
            # Write updated configuration
            self.write_config_file(new_config)
            
            # Reload config module
            import importlib
            importlib.reload(config)
            
            self.config_status_label.config(text="Configuration saved successfully!", foreground="green")
            
            # Show restart recommendation
            restart_msg = ("Configuration saved!\n\n"
                          "Some changes may require restarting the system to take effect.\n"
                          "Would you like to restart the system now?")
            
            if messagebox.askyesno("Restart System?", restart_msg):
                self.restart_system()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            self.config_status_label.config(text="Save failed", foreground="red")
    
    def write_config_file(self, new_config):
        """Write the new configuration to config.py file"""
        # Read the current file
        with open('config.py', 'r') as f:
            lines = f.readlines()
        
        # Process each line and replace configuration values
        new_lines = []
        for line in lines:
            line_stripped = line.strip()
            
            # Check if this line contains a configuration we want to update
            updated = False
            for key, value in new_config.items():
                if line_stripped.startswith(f"{key} = "):
                    # Replace the line with new value
                    if isinstance(value, dict):
                        new_lines.append(f"{key} = {repr(value)}\n")
                    elif isinstance(value, list):
                        new_lines.append(f"{key} = {repr(value)}\n")
                    elif isinstance(value, str):
                        new_lines.append(f"{key} = {repr(value)}\n")
                    else:
                        new_lines.append(f"{key} = {value}\n")
                    updated = True
                    break
            
            if not updated:
                new_lines.append(line)
        
        # Write the updated file
        with open('config.py', 'w') as f:
            f.writelines(new_lines)
    
    def reset_config(self):
        """Reset configuration editor to current values"""
        self.load_current_config()
    
    def load_config_file(self):
        """Load configuration from a file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("Python files", "*.py"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'r') as f:
                        data = json.load(f)
                    # Apply JSON data to config vars
                    messagebox.showinfo("Info", "JSON configuration loading not fully implemented yet")
                else:
                    messagebox.showinfo("Info", "Please select the config.py file to load")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration file: {e}")
    
    def restart_system(self):
        """Restart the system with new configuration"""
        if self.system:
            self.add_log("Restarting system with new configuration...")
            self.system.stop()
            time.sleep(2)  # Give time to stop
            self.start_system()
    
    # All the original methods remain the same...
    def create_status_frame(self, parent):
        """Create system status display"""
        status_frame = ttk.LabelFrame(parent, text="System Status", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status labels
        self.status_label = ttk.Label(status_frame, text="System: Starting...", 
                                     font=('Arial', 12, 'bold'))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.ec_ph_label = ttk.Label(status_frame, text="EC: -- mS/cm, pH: --")
        self.ec_ph_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Emergency stop button
        emergency_btn = ttk.Button(status_frame, text="🚨 EMERGENCY STOP 🚨", 
                                  command=self.emergency_stop)
        emergency_btn.grid(row=0, column=2, sticky=tk.E, padx=(20, 0))
        
        status_frame.columnconfigure(1, weight=1)
    
    def create_control_frames(self, parent):
        """Create control panels"""
        
        # Left column - Pumps and Relays
        left_frame = ttk.Frame(parent)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.rowconfigure(1, weight=1)
        
        # Right column - Flow meters and EC/pH
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.rowconfigure(1, weight=1)
        
        # Pump control
        self.create_pump_control(left_frame)
        
        # Relay control
        self.create_relay_control(left_frame)
        
        # Flow meter control
        self.create_flow_control(right_frame)
        
        # EC/pH control
        self.create_ecph_control(right_frame)
    
    def create_pump_control(self, parent):
        """Create pump control panel"""
        pump_frame = ttk.LabelFrame(parent, text="Pump Control", padding="10")
        pump_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Pump selection
        ttk.Label(pump_frame, text="Pump:").grid(row=0, column=0, sticky=tk.W)
        
        available_pumps = get_available_pumps()
        self.pump_var = tk.IntVar(value=available_pumps[0] if available_pumps else 1)
        pump_combo = ttk.Combobox(pump_frame, textvariable=self.pump_var, 
                                 values=available_pumps, state="readonly", width=5)
        pump_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Amount entry with validation
        ttk.Label(pump_frame, text="Amount (ml):").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.amount_var = tk.StringVar(value="10.0")
        amount_entry = ttk.Entry(pump_frame, textvariable=self.amount_var, width=10)
        amount_entry.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Volume limits label
        limits_label = ttk.Label(pump_frame, text=f"({MIN_PUMP_VOLUME_ML}-{MAX_PUMP_VOLUME_ML}ml)", 
                                font=('Arial', 8), foreground="gray")
        limits_label.grid(row=0, column=4, sticky=tk.W, padx=(5, 0))
        
        # Buttons
        dispense_btn = ttk.Button(pump_frame, text="Dispense", command=self.dispense_pump)
        dispense_btn.grid(row=0, column=5, padx=(10, 0))
        
        stop_btn = ttk.Button(pump_frame, text="Stop", command=self.stop_pump)
        stop_btn.grid(row=0, column=6, padx=(5, 0))
        
        # Status display
        self.pump_status_label = ttk.Label(pump_frame, text="Status: Idle")
        self.pump_status_label.grid(row=1, column=0, columnspan=7, sticky=tk.W, pady=(10, 0))
        
        # Pump info display
        self.pump_info_label = ttk.Label(pump_frame, text="", foreground="blue")
        self.pump_info_label.grid(row=2, column=0, columnspan=7, sticky=tk.W)
        
        # Update pump info when selection changes
        def update_pump_info(*args):
            pump_id = self.pump_var.get()
            pump_name = get_pump_name(pump_id)
            self.pump_info_label.config(text=f"Selected: Pump {pump_id} - {pump_name}")
        
        self.pump_var.trace('w', update_pump_info)
        update_pump_info()  # Initial update
    
    def create_relay_control(self, parent):
        """Create relay control panel using config"""
        relay_frame = ttk.LabelFrame(parent, text="Relay Control", padding="10")
        relay_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create scrollable frame for relays
        canvas = tk.Canvas(relay_frame)
        scrollbar = ttk.Scrollbar(relay_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Relay buttons using config
        self.relay_buttons = {}
        available_relays = get_available_relays()
        
        for relay_id in sorted(available_relays):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=2)
            
            relay_name = get_relay_name(relay_id)
            label = ttk.Label(frame, text=f"{relay_id:2d}. {relay_name}:", width=25, anchor="w")
            label.pack(side=tk.LEFT)
            
            on_btn = ttk.Button(frame, text="ON", width=6,
                               command=lambda r=relay_id: self.control_relay(r, True))
            on_btn.pack(side=tk.LEFT, padx=(5, 2))
            
            off_btn = ttk.Button(frame, text="OFF", width=6,
                                command=lambda r=relay_id: self.control_relay(r, False))
            off_btn.pack(side=tk.LEFT, padx=(2, 5))
            
            status_label = ttk.Label(frame, text="OFF", width=6, anchor="center")
            status_label.pack(side=tk.LEFT, padx=(5, 0))
            
            self.relay_buttons[relay_id] = {
                'on': on_btn,
                'off': off_btn,
                'status': status_label
            }
        
        # All relays off button
        all_off_frame = ttk.Frame(scrollable_frame)
        all_off_frame.pack(fill=tk.X, pady=(10, 0))
        all_off_btn = ttk.Button(all_off_frame, text="ALL RELAYS OFF", 
                                command=lambda: self.control_relay(0, False))
        all_off_btn.pack(fill=tk.X)
        
        # Mock warning if using mock hardware
        if MOCK_SETTINGS.get('relays', False):
            mock_label = ttk.Label(scrollable_frame, text="⚠️ Using Mock Relays", 
                                  foreground="orange", font=('Arial', 9, 'italic'))
            mock_label.pack(pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_flow_control(self, parent):
        """Create flow meter control panel using config"""
        flow_frame = ttk.LabelFrame(parent, text="Flow Meter Control", padding="10")
        flow_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Flow meter selection
        ttk.Label(flow_frame, text="Flow Meter:").grid(row=0, column=0, sticky=tk.W)
        
        available_flows = get_available_flow_meters()
        self.flow_var = tk.IntVar(value=available_flows[0] if available_flows else 1)
        flow_combo = ttk.Combobox(flow_frame, textvariable=self.flow_var,
                                 values=available_flows, state="readonly", width=5)
        flow_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Gallons entry with validation
        ttk.Label(flow_frame, text="Gallons:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.gallons_var = tk.StringVar(value="5")
        gallons_entry = ttk.Entry(flow_frame, textvariable=self.gallons_var, width=10)
        gallons_entry.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Flow limits label
        limits_label = ttk.Label(flow_frame, text=f"(max {MAX_FLOW_GALLONS})", 
                                font=('Arial', 8), foreground="gray")
        limits_label.grid(row=0, column=4, sticky=tk.W, padx=(5, 0))
        
        # Buttons
        start_flow_btn = ttk.Button(flow_frame, text="Start Flow", command=self.start_flow)
        start_flow_btn.grid(row=0, column=5, padx=(10, 0))
        
        stop_flow_btn = ttk.Button(flow_frame, text="Stop Flow", command=self.stop_flow)
        stop_flow_btn.grid(row=0, column=6, padx=(5, 0))
        
        # Status display
        self.flow_status_label = ttk.Label(flow_frame, text="Status: Inactive")
        self.flow_status_label.grid(row=1, column=0, columnspan=7, sticky=tk.W, pady=(10, 0))
        
        # Flow meter info display
        self.flow_info_label = ttk.Label(flow_frame, text="", foreground="blue")
        self.flow_info_label.grid(row=2, column=0, columnspan=7, sticky=tk.W)
        
        # Update flow meter info when selection changes
        def update_flow_info(*args):
            meter_id = self.flow_var.get()
            meter_name = get_flow_meter_name(meter_id)
            self.flow_info_label.config(text=f"Selected: Flow Meter {meter_id} - {meter_name}")
        
        self.flow_var.trace('w', update_flow_info)
        update_flow_info()  # Initial update
        
        # Mock warning if using mock hardware
        if MOCK_SETTINGS.get('flow_meters', False):
            mock_label = ttk.Label(flow_frame, text="⚠️ Using Mock Flow Meters", 
                                  foreground="orange", font=('Arial', 9, 'italic'))
            mock_label.grid(row=3, column=0, columnspan=7, pady=5)
    
    def create_ecph_control(self, parent):
        """Create EC/pH control panel using config"""
        ecph_frame = ttk.LabelFrame(parent, text="EC/pH Control", padding="10")
        ecph_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Monitoring buttons
        btn_frame = ttk.Frame(ecph_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        start_monitor_btn = ttk.Button(btn_frame, text="Start Monitoring", 
                                      command=self.start_ecph_monitoring)
        start_monitor_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        stop_monitor_btn = ttk.Button(btn_frame, text="Stop Monitoring", 
                                     command=self.stop_ecph_monitoring)
        stop_monitor_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Readings display
        readings_frame = ttk.Frame(ecph_frame)
        readings_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.ec_reading_label = ttk.Label(readings_frame, text="EC: -- mS/cm", 
                                         font=('Arial', 14))
        self.ec_reading_label.pack(anchor=tk.W)
        
        self.ph_reading_label = ttk.Label(readings_frame, text="pH: --", 
                                         font=('Arial', 14))
        self.ph_reading_label.pack(anchor=tk.W)
        
        # Calibration section using config
        cal_frame = ttk.LabelFrame(ecph_frame, text="Calibration", padding="5")
        cal_frame.pack(fill=tk.X)
        
        # pH calibration using configured solutions
        ph_cal_frame = ttk.Frame(cal_frame)
        ph_cal_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(ph_cal_frame, text="pH Cal:").pack(side=tk.LEFT)
        
        # Create pH calibration buttons from config
        for cal_type, value in PH_CALIBRATION_SOLUTIONS.items():
            btn_text = f"pH {value}" if value else cal_type.title()
            ttk.Button(ph_cal_frame, text=btn_text, width=6,
                      command=lambda ct=cal_type, v=str(value): self.calibrate_ph(ct, v)).pack(side=tk.LEFT, padx=2)
        
        # EC calibration using configured solutions
        ec_cal_frame = ttk.Frame(cal_frame)
        ec_cal_frame.pack(fill=tk.X)
        
        ttk.Label(ec_cal_frame, text="EC Cal:").pack(side=tk.LEFT)
        
        # Create EC calibration buttons from config
        for cal_type, value in EC_CALIBRATION_SOLUTIONS.items():
            if cal_type == "dry":
                btn_text = "Dry"
                cmd = lambda: self.calibrate_ec("dry")
            else:
                btn_text = str(value)
                cmd = lambda ct=cal_type, v=str(value): self.calibrate_ec(ct, v)
            
            ttk.Button(ec_cal_frame, text=btn_text, width=6, command=cmd).pack(side=tk.LEFT, padx=2)
        
        # Mock warning if using mock hardware
        if MOCK_SETTINGS.get('arduino', False):
            mock_label = ttk.Label(ecph_frame, text="⚠️ Using Mock Arduino", 
                                  foreground="orange", font=('Arial', 9, 'italic'))
            mock_label.pack(pady=5)
    
    def create_log_frame(self, parent):
        """Create log display"""
        log_frame = ttk.LabelFrame(parent, text="System Log", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log control buttons
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        clear_log_btn = ttk.Button(log_btn_frame, text="Clear Log", command=self.clear_log)
        clear_log_btn.pack(side=tk.LEFT)
        
        save_log_btn = ttk.Button(log_btn_frame, text="Save Log", command=self.save_log)
        save_log_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Show configuration button
        config_btn = ttk.Button(log_btn_frame, text="Show Config", command=self.show_config)
        config_btn.pack(side=tk.LEFT, padx=(5, 0))
    
    def start_system(self):
        """Start the feed control system in background thread"""
        # First add a log entry in the main thread
        self.add_log("Initializing feed control system with config.py...")
        
        def init_system():
            try:
                # Use mock settings from config
                use_mock_flow = MOCK_SETTINGS.get('flow_meters', False)
                self.system = FeedControlSystem(use_mock_flow=use_mock_flow)
                self.system.set_message_callback(self.system_message_callback)
                self.system.start()
                self.system_running = True
                # Use after() to update GUI from the main thread
                self.root.after(0, lambda: self.add_log("✓ System started successfully"))
            except Exception as e:
                error_msg = f"✗ System startup failed: {e}"
                error_details = f"Failed to start system:\n{e}"
                # Use after() to update GUI from the main thread
                self.root.after(0, lambda: self.add_log(error_msg))
                self.root.after(0, lambda msg=error_details: messagebox.showerror("System Error", msg))
        
        # Now start the thread after we're in the main loop
        thread = threading.Thread(target=init_system, daemon=True)
        thread.start()
    
    def system_message_callback(self, message):
        """Handle messages from the system"""
        self.root.after(0, lambda: self.add_log(f"SYS: {message}"))
    
    def add_log(self, message):
        """Add message to log"""
        # Check if we're in the main thread
        if threading.current_thread() is threading.main_thread():
            # Direct update if we're in the main thread
            timestamp = datetime.now().strftime('%H:%M:%S')
            formatted_message = f"[{timestamp}] {message}"
            self.log_text.insert(tk.END, formatted_message + "\n")
            self.log_text.see(tk.END)
        else:
            # Schedule update on the main thread if we're in a background thread
            self.root.after(0, lambda msg=message: self.add_log_main_thread(msg))
    
    def add_log_main_thread(self, message):
        """Add log message from the main thread"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
    
    def save_log(self):
        """Save log to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.add_log(f"Log saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save log:\n{e}")
    
    def show_config(self):
        """Show current configuration"""
        config_info = []
        config_info.append("=== SYSTEM CONFIGURATION ===")
        config_info.append(f"Available Pumps: {get_available_pumps()}")
        config_info.append(f"Available Relays: {get_available_relays()}")  
        config_info.append(f"Available Flow Meters: {get_available_flow_meters()}")
        config_info.append("")
        config_info.append("Mock Settings:")
        for component, enabled in MOCK_SETTINGS.items():
            status = "ENABLED" if enabled else "disabled"
            config_info.append(f"  {component}: {status}")
        config_info.append("")
        config_info.append("Pump Volume Limits: {}-{}ml".format(MIN_PUMP_VOLUME_ML, MAX_PUMP_VOLUME_ML))
        config_info.append(f"Max Flow Gallons: {MAX_FLOW_GALLONS}")
        
        for line in config_info:
            self.add_log(line)
    
    def update_status(self):
        """Update system status display"""
        if self.system and self.system_running:
            try:
                # Update system status
                status = self.system.get_system_status()
                
                # Main status
                self.status_label.config(text="System: Running ✓", foreground="green")
                
                # EC/pH readings
                ec_ph = status.get('ec_ph', {})
                ec = ec_ph.get('ec', '--')
                ph = ec_ph.get('ph', '--')
                self.ec_ph_label.config(text=f"EC: {ec} mS/cm, pH: {ph}")
                
                # Update EC/pH display
                if ec != '--':
                    self.ec_reading_label.config(text=f"EC: {ec:.2f} mS/cm")
                if ph != '--':
                    self.ph_reading_label.config(text=f"pH: {ph:.2f}")
                
                # Update relay states
                relays = status.get('relays', {})
                for relay_id, state in relays.items():
                    if relay_id in self.relay_buttons:
                        status_text = "ON" if state else "OFF"
                        color = "green" if state else "red"
                        self.relay_buttons[relay_id]['status'].config(
                            text=status_text, foreground=color
                        )
                
                # Update pump status
                pumps = status.get('pumps', {})
                current_pump = self.pump_var.get()
                if current_pump in pumps:
                    pump_info = pumps[current_pump]
                    if pump_info and pump_info['is_dispensing']:
                        current = pump_info['current_volume']
                        target = pump_info['target_volume']
                        self.pump_status_label.config(
                            text=f"Status: Dispensing {current:.1f}/{target:.1f} ml",
                            foreground="orange"
                        )
                    else:
                        self.pump_status_label.config(
                            text="Status: Idle",
                            foreground="black"
                        )
                
                # Update flow status
                flows = status.get('flow_meters', {})
                current_flow = self.flow_var.get()
                if current_flow in flows:
                    flow_info = flows[current_flow]
                    if flow_info['status'] == 1:  # Active
                        current = flow_info['current_gallons']
                        target = flow_info['target_gallons']
                        self.flow_status_label.config(
                            text=f"Status: Active {current}/{target} gallons",
                            foreground="orange"
                        )
                    else:
                        self.flow_status_label.config(
                            text="Status: Inactive",
                            foreground="black"
                        )
            
            except Exception as e:
                self.add_log(f"Status update error: {e}")
        else:
            self.status_label.config(text="System: Not Running", foreground="red")
        
        # Schedule next update
        self.root.after(1000, self.update_status)
    
    # Control methods with validation
    def control_relay(self, relay_id, state):
        """Control relay with validation"""
        if not self.system:
            return
        
        # Validate relay ID
        if relay_id != 0 and relay_id not in get_available_relays():
            messagebox.showerror("Error", f"Invalid relay ID: {relay_id}")
            return
        
        state_str = "ON" if state else "OFF"
        command = f"Start;Relay;{relay_id};{state_str};end"
        success = self.system.send_command(command)
        
        if success:
            if relay_id == 0:
                self.add_log(f"Command sent: All relays {state_str}")
            else:
                relay_name = get_relay_name(relay_id)
                self.add_log(f"Command sent: {relay_name} {state_str}")
        else:
            self.add_log(f"Failed to send relay command")
    
    def dispense_pump(self):
        """Start pump dispense with validation"""
        if not self.system:
            return
        
        try:
            pump_id = self.pump_var.get()
            amount = float(self.amount_var.get())
            
            # Validate pump ID
            if pump_id not in get_available_pumps():
                messagebox.showerror("Error", f"Invalid pump ID: {pump_id}")
                return
            
            # Validate amount
            if not (MIN_PUMP_VOLUME_ML <= amount <= MAX_PUMP_VOLUME_ML):
                messagebox.showerror("Error", 
                    f"Amount must be between {MIN_PUMP_VOLUME_ML} and {MAX_PUMP_VOLUME_ML}ml")
                return
            
            command = f"Start;Dispense;{pump_id};{amount};end"
            success = self.system.send_command(command)
            
            if success:
                pump_name = get_pump_name(pump_id)
                self.add_log(f"Dispensing {amount}ml from {pump_name}")
            else:
                self.add_log(f"Failed to start dispense")
        
        except ValueError:
            messagebox.showerror("Input Error", "Invalid amount value")
    
    def stop_pump(self):
        """Stop pump"""
        if not self.system:
            return
        
        pump_id = self.pump_var.get()
        command = f"Start;Pump;{pump_id};X;end"
        success = self.system.send_command(command)
        
        if success:
            pump_name = get_pump_name(pump_id)
            self.add_log(f"Stopped {pump_name}")
    
    def start_flow(self):
        """Start flow monitoring with validation"""
        if not self.system:
            return
        
        try:
            flow_id = self.flow_var.get()
            gallons = int(self.gallons_var.get())
            
            # Validate flow meter ID
            if flow_id not in get_available_flow_meters():
                messagebox.showerror("Error", f"Invalid flow meter ID: {flow_id}")
                return
            
            # Validate gallons
            if not (1 <= gallons <= MAX_FLOW_GALLONS):
                messagebox.showerror("Error", f"Gallons must be between 1 and {MAX_FLOW_GALLONS}")
                return
            
            command = f"Start;StartFlow;{flow_id};{gallons};220;end"
            success = self.system.send_command(command)
            
            if success:
                meter_name = get_flow_meter_name(flow_id)
                self.add_log(f"Started {meter_name} for {gallons} gallons")
        
        except ValueError:
            messagebox.showerror("Input Error", "Invalid gallons value")
    
    def stop_flow(self):
        """Stop flow monitoring"""
        if not self.system:
            return
        
        flow_id = self.flow_var.get()
        command = f"Start;StartFlow;{flow_id};0;end"
        success = self.system.send_command(command)
        
        if success:
            meter_name = get_flow_meter_name(flow_id)
            self.add_log(f"Stopped {meter_name}")
    
    def start_ecph_monitoring(self):
        """Start EC/pH monitoring"""
        if not self.system:
            return
        
        command = "Start;EcPh;ON;end"
        success = self.system.send_command(command)
        
        if success:
            self.add_log("Started EC/pH monitoring")
    
    def stop_ecph_monitoring(self):
        """Stop EC/pH monitoring"""
        if not self.system:
            return
        
        command = "Start;EcPh;OFF;end"
        success = self.system.send_command(command)
        
        if success:
            self.add_log("Stopped EC/pH monitoring")
    
    def calibrate_ph(self, cal_type, value):
        """Calibrate pH sensor using config values"""
        if not self.system or not self.system.uno_controller:
            self.add_log("Arduino Uno not available for pH calibration")
            return
        
        success = self.system.uno_controller.calibrate_ph(cal_type, value)
        if success:
            self.add_log(f"pH calibration: {cal_type} = {value}")
    
    def calibrate_ec(self, cal_type, value=None):
        """Calibrate EC sensor using config values"""
        if not self.system or not self.system.uno_controller:
            self.add_log("Arduino Uno not available for EC calibration")
            return
        
        success = self.system.uno_controller.calibrate_ec(cal_type, value)
        if success:
            cal_str = f"{cal_type} = {value}" if value else cal_type
            self.add_log(f"EC calibration: {cal_str}")
    
    def emergency_stop(self):
        """Emergency stop all operations"""
        if not self.system:
            return
        
        self.system.emergency_stop()
        self.add_log("🚨 EMERGENCY STOP ACTIVATED 🚨")
        messagebox.showwarning("Emergency Stop", "All operations have been stopped!")
    
    def on_closing(self):
        """Handle window closing"""
        if self.system:
            self.add_log("Shutting down system...")
            self.system.stop()
        
        self.root.destroy()


def main():
    """Main entry point for GUI"""
    root = tk.Tk()
    app = FeedControlGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Start GUI
    root.mainloop()


if __name__ == "__main__":
    main()