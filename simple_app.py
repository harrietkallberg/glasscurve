# simple_app.py
from flask import Flask, render_template, request, send_file
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web
import matplotlib.pyplot as plt
import io
import base64
from firing_curve import GlassTypeHandler

app = Flask(__name__)

# Initialize your existing glass handler
glass_handler = GlassTypeHandler('tables.json')

@app.route('/')
def home():
    # Get glass types for the dropdown
    glass_types = glass_handler.glass_data["Glassorter"]
    return render_template('index.html', glass_types=glass_types)

@app.route('/create_curve', methods=['POST'])
def create_curve():
    # Get form data
    glass_choice = int(request.form['glass_choice'])
    oven_type = request.form['oven_type']
    radius = int(request.form['radius'])
    layers = int(request.form['layers'])
    minutes = int(request.form['minutes'])
    room_temp = int(request.form['room_temp'])
    firing_type = request.form['firing_type']
    
    # Get the selected glass info
    glass_info = glass_handler.glass_data["Glassorter"][glass_choice - 1]
    
    # Use your existing logic to create the curve
    try:
        # Extract the tables (same as your existing code)
        uppvarmning_table = next(
            item["tabell"] for item in glass_handler.glass_data["Tider for uppvarmning"]
            if item["kategori"] == glass_info["kategori"] and item["ugn"] == oven_type
        )
        
        halltider_table = next(
            item["tabell"] for item in glass_handler.glass_data["Halltider"]
            if item["kategori"] == glass_info["kategori"]
        )
        
        avspanning_table = next(
            item["tabell"] for item in glass_handler.glass_data["Avspanningstider"]
            if item["kategori"] == glass_info["kategori"]
        )
        
        # Get times from tables
        uppvarmning_time = glass_handler.get_time_from_table(uppvarmning_table, radius, layers)
        halltider_time = glass_handler.get_time_from_table(halltider_table, radius, layers)
        avspanning_time = glass_handler.get_time_from_table(avspanning_table, radius, layers)
        
        # Determine top temperature
        if firing_type == "f":
            topptemp = round((glass_info["f_topptemp"][0] + glass_info["f_topptemp"][1]) / 2)
        elif firing_type == "s":
            topptemp = round((glass_info["s_topptemp"][0] + glass_info["s_topptemp"][1]) / 2)
        else:  # firing_type == "t"
            topptemp = glass_info["t_topptemp"]
        
        # Create the firing curve (adapted from your existing code)
        curve = create_firing_curve(glass_info, uppvarmning_time, halltider_time, 
                                  avspanning_time, topptemp, minutes, room_temp)
        
        # Generate the plot
        plot_url = create_plot_base64(curve)
        
        # Get phase details for display
        phases = []
        for i, phase in enumerate(curve):
            phases.append({
                'phase_num': i + 1,
                'start_temp': phase._startTemp,
                'end_temp': phase._endTemp,
                'velocity': phase._velocity,
                'holding_time': phase._holdingTime,
                'time': phase._time
            })
        
        return render_template('result.html', 
                             plot_url=plot_url, 
                             phases=phases, 
                             total_time=curve.getTotalTime(),
                             glass_info=glass_info,
                             parameters={
                                 'oven_type': 'toppvärmd' if oven_type == 't' else 'sidovärmd',
                                 'radius': radius,
                                 'layers': layers,
                                 'minutes': minutes,
                                 'room_temp': room_temp,
                                 'firing_type': {'f': 'fullfusing', 's': 'slumping', 't': 'tackfusing'}[firing_type]
                             })
    
    except Exception as e:
        return f"Ett fel uppstod: {str(e)}", 400

def create_firing_curve(glass_info, uppvarmning_time, halltider_time, avspanning_time, topptemp, minutes, room_temp):
    """Create firing curve - adapted from your existing code"""
    import numpy as np
    from firing_curve import firingCurve
    
    o_astemp = glass_info["o_astemp"]
    n_astemp = glass_info["n_astemp"]
    inledande_smaltpunkt = glass_handler.glass_data["Inledande_smaltpunkt"]
    
    # Calculate velocities
    first_heating_velocity = 999 if np.trunc(60*(inledande_smaltpunkt - room_temp)/uppvarmning_time) >= 999 else np.trunc(60*(inledande_smaltpunkt - room_temp)/uppvarmning_time)
    second_heating_velocity = 999
    first_cooling_velocity = np.trunc(60*(o_astemp - topptemp)/halltider_time)
    second_cooling_velocity = np.trunc(60*(n_astemp - o_astemp)/avspanning_time)
    last_cooling_velocity = -20
    
    # Create curve
    curve = firingCurve(room_temp)
    curve.newPhase(first_heating_velocity, inledande_smaltpunkt)
    curve.newPhase(second_heating_velocity, topptemp, minutes)
    curve.newPhase(first_cooling_velocity, o_astemp)
    curve.newPhase(second_cooling_velocity, n_astemp)
    curve.newPhase(last_cooling_velocity, room_temp)
    
    return curve

def create_plot_base64(curve):
    """Generate plot and return as base64 string for embedding in HTML"""
    # Adapted from your existing plotting code
    total_time = 0
    current_temp = curve._roomTemp

    plt.figure(figsize=(12, 8))
    cmap = plt.get_cmap('tab20')

    times = [0]
    temperatures = [current_temp]

    for idx, phase in enumerate(curve):
        if phase._color is None:
            phase._color = cmap(idx % 20)

        phase_time = phase._time
        middle_time = None
        if phase._holdingTime != 0:
            phase_holdingTime = phase._holdingTime
            middle_time = total_time + phase_time - phase_holdingTime
        start_time = total_time
        end_time = total_time + phase_time
        total_time = end_time

        if middle_time:
            time_points = [start_time, middle_time, end_time]
        else:
            time_points = [start_time, end_time]

        if phase._velocity == 0:
            temp_points = [current_temp, current_temp]
        else:
            if middle_time:
                temp_points = [current_temp, phase._endTemp, phase._endTemp]
            else:
                temp_points = [current_temp, phase._endTemp]

        plt.plot(time_points, temp_points, marker='o', color=phase._color, 
                label=f'Fas {idx+1}', linewidth=2, markersize=6)
        current_temp = phase._endTemp

    plt.title('Brännkurva', fontsize=16, fontweight='bold')
    plt.xlabel('Tid (minuter)', fontsize=12)
    plt.ylabel('Temperatur (°C)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(title='Faser', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # Convert to base64 for embedding
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    plot_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    return f"data:image/png;base64,{plot_base64}"

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)