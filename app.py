import os
from flask import Flask, render_template, request, jsonify
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Railway
import matplotlib.pyplot as plt
from firing_curve import GlassTypeHandler, firingCurve
import matplotlib.colors as mcolors

app = Flask(__name__)

@app.route('/')
def index():
    """Main page with web interface"""
    try:
        return render_template('index.html')
    except Exception as e:
        # If template doesn't exist, return a simple HTML page
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Glass Firing Curve Generator</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                button { padding: 15px 30px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
                button:hover { background: #0056b3; }
                #result { margin-top: 20px; }
                img { max-width: 100%; border: 1px solid #ddd; margin: 10px 0; }
            </style>
        </head>
        <body>
            <h1>🔥 Glass Firing Curve Generator</h1>
            <p>Verktyg för Dalarnas Glasverkstad</p>
            
            <button onclick="createCurve()">Skapa Brännkurva</button>
            
            <div id="result"></div>

            <script>
                function createCurve() {
                    document.getElementById('result').innerHTML = '<p>Skapar brännkurva...</p>';
                    
                    fetch('/api/create-curve', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        if(data.success) {
                            document.getElementById('result').innerHTML = 
                                '<h2>✅ Brännkurva Skapad!</h2><img src="data:image/png;base64,' + data.plot + '">';
                        } else {
                            document.getElementById('result').innerHTML = '<p style="color:red;">❌ Fel: ' + data.error + '</p>';
                        }
                    })
                    .catch(error => {
                        document.getElementById('result').innerHTML = '<p style="color:red;">❌ Fel: ' + error.message + '</p>';
                    });
                }
            </script>
        </body>
        </html>
        '''

@app.route('/api/glass-types')
def get_glass_types():
    """Get available glass types from JSON"""
    try:
        handler = GlassTypeHandler('tables.json')
        glass_types = handler.glass_data["Glassorter"]
        return jsonify({'success': True, 'glass_types': glass_types})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create-curve', methods=['POST'])
def create_firing_curve():
    """Create firing curve with default parameters (simplified for web)"""
    try:
        # Create a simplified version that doesn't require user input
        # We'll use default parameters for Bullseye 90 glass
        
        # Load glass data
        handler = GlassTypeHandler('tables.json')
        glass_data = handler.glass_data
        
        # Use default parameters (you can modify these or add form inputs later)
        glass_info = glass_data["Glassorter"][0]  # Bullseye 90
        oven_type = 't'  # toppvärmd
        radius = 20
        layers = 2
        minutes = 5
        room_temp = 20
        firing_type = 'f'  # fullfusing
        
        # Calculate temperatures
        if firing_type == "f":
            topptemp = round((glass_info.get("f_topptemp")[0] + glass_info.get("f_topptemp")[1]) / 2)
        elif firing_type == "s":
            topptemp = round((glass_info.get("s_topptemp")[0] + glass_info.get("s_topptemp")[1]) / 2)
        elif firing_type == "t":
            topptemp = glass_info.get("t_topptemp")
        
        # Get timing tables
        uppvarmning_table = next(
            item["tabell"] for item in glass_data["Tider for uppvarmning"]
            if item["kategori"] == glass_info["kategori"] and item["ugn"] == oven_type
        )
        
        halltider_table = next(
            item["tabell"] for item in glass_data["Halltider"]
            if item["kategori"] == glass_info["kategori"]
        )
        
        avspanning_table = next(
            item["tabell"] for item in glass_data["Avspanningstider"]
            if item["kategori"] == glass_info["kategori"]
        )
        
        # Get times from tables
        def get_time_from_table(table, radius, layers):
            for row in table:
                if str(radius) in row:
                    return row[str(radius)][str(layers)]
            raise ValueError("Radius or layers not found in the table")
        
        uppvarmning_time = get_time_from_table(uppvarmning_table, radius, layers)
        halltider_time = get_time_from_table(halltider_table, radius, layers)
        avspanning_time = get_time_from_table(avspanning_table, radius, layers)
        
        # Create firing curve
        o_astemp = glass_info.get("o_astemp")
        n_astemp = glass_info.get("n_astemp")
        inledande_smaltpunkt = glass_data["Inledande_smaltpunkt"]
        
        import numpy as np
        first_heating_velocity = 999 if np.trunc(60*(inledande_smaltpunkt - room_temp)/uppvarmning_time) >= 999 else np.trunc(60*(inledande_smaltpunkt - room_temp)/uppvarmning_time)
        second_heating_velocity = 999
        first_cooling_velocity = np.trunc(60*(o_astemp - topptemp)/halltider_time)
        second_cooling_velocity = np.trunc(60*(n_astemp - o_astemp)/avspanning_time)
        last_cooling_velocity = -20
        
        curve = firingCurve(room_temp)
        curve.newPhase(first_heating_velocity, inledande_smaltpunkt)
        curve.newPhase(second_heating_velocity, topptemp, minutes)
        curve.newPhase(first_cooling_velocity, o_astemp)
        curve.newPhase(second_cooling_velocity, n_astemp)
        curve.newPhase(last_cooling_velocity, room_temp)
        
        # Generate plot
        total_time = 0
        current_temp = curve._roomTemp
        
        plt.figure(figsize=(12, 8))
        
        # Create a colormap
        cmap = plt.get_cmap('tab20')
        
        for idx, phase in enumerate(curve):
            # Assign a color if it's not already set
            if phase._color is None:
                phase._color = cmap(idx % 20)
            
            # Calculate time increment for the phase
            phase_time = phase._time
            middle_time = None
            if phase._holdingTime != 0:
                phase_holdingTime = phase._holdingTime
                middle_time = total_time + phase_time - phase_holdingTime
            start_time = total_time
            end_time = total_time + phase_time
            total_time = end_time
            
            # Time points for this phase
            if middle_time:
                time_points = [start_time, middle_time, end_time]
            else:
                time_points = [start_time, end_time]
            
            # Temperature points for this phase
            if phase._velocity == 0:
                # Holding phase
                temp_points = [current_temp, current_temp]
            else:
                if middle_time:
                    temp_points = [current_temp, phase._endTemp, phase._endTemp]
                else:
                    temp_points = [current_temp, phase._endTemp]
            
            # Plot this phase
            plt.plot(time_points, temp_points, marker='o', color=phase._color, 
                    linewidth=2, markersize=6, label=f'Fas {idx+1}')
            
            # Update current temperature
            current_temp = phase._endTemp
        
        plt.title(f'Brännkurva för {glass_info["namn"]} - {firing_type.upper()}', fontsize=16, fontweight='bold')
        plt.xlabel('Tid (minuter)', fontsize=12)
        plt.ylabel('Temperatur (°C)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(title='Faser', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        # Convert plot to base64 string
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=150)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        # Get phase information
        phases = []
        for i in range(curve._totalPhases):
            phase = curve.findPhase(i)
            
            # Get color hex
            if phase._color is not None:
                color_hex = mcolors.to_hex(phase._color)
            else:
                color_hex = '#000000'
            
            phases.append({
                'phase': i + 1,
                'start_temp': phase._startTemp,
                'end_temp': phase._endTemp,
                'velocity': phase._velocity,
                'holding_time': phase._holdingTime,
                'time': phase._time,
                'color': color_hex
            })
        
        return jsonify({
            'success': True,
            'plot': plot_url,
            'phases': phases,
            'total_time': curve.getTotalTime(),
            'glass_type': glass_info["namn"],
            'firing_type': firing_type,
            'parameters': {
                'radius': radius,
                'layers': layers,
                'minutes': minutes,
                'room_temp': room_temp,
                'oven_type': 'toppvärmd' if oven_type == 't' else 'sidovärmd'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({'status': 'healthy', 'app': 'Glass Firing Curve Generator'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)