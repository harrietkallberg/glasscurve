import os
from flask import Flask, render_template, request, jsonify
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Railway
import matplotlib.pyplot as plt
from firing_curve import GlassTypeHandler, firingCurve
import matplotlib.colors as mcolors
import numpy as np
import json

app = Flask(__name__)

def ensure_serializable(value):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    return value

@app.route('/')
def index():
    """Main page with web interface"""
    try:
        return render_template('index.html')
    except Exception as e:
        # If template doesn't exist, return a comprehensive HTML page
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Glass Firing Curve Generator</title>
            <meta charset="UTF-8">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f5f5f5;
                    line-height: 1.6;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { 
                    color: #333; 
                    text-align: center;
                    margin-bottom: 10px;
                }
                .subtitle {
                    text-align: center;
                    color: #666;
                    margin-bottom: 30px;
                    font-style: italic;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #333;
                }
                select, input {
                    width: 100%;
                    padding: 10px;
                    border: 2px solid #ddd;
                    border-radius: 5px;
                    font-size: 16px;
                    box-sizing: border-box;
                }
                select:focus, input:focus {
                    border-color: #007bff;
                    outline: none;
                }
                button {
                    width: 100%;
                    padding: 15px;
                    font-size: 18px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    margin-top: 20px;
                }
                button:hover {
                    background: #0056b3;
                }
                button:disabled {
                    background: #ccc;
                    cursor: not-allowed;
                }
                #result {
                    margin-top: 30px;
                }
                img {
                    max-width: 100%;
                    border: 1px solid #ddd;
                    margin: 20px 0;
                    border-radius: 5px;
                }
                .loading {
                    text-align: center;
                    color: #007bff;
                    font-size: 18px;
                }
                .error {
                    color: #dc3545;
                    background: #f8d7da;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #f5c6cb;
                }
                .success {
                    color: #155724;
                    background: #d4edda;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #c3e6cb;
                    margin-bottom: 20px;
                }
                .phase-info {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #007bff;
                }
                .phase-info h3 {
                    margin-top: 0;
                    color: #007bff;
                }
                .parameter-info {
                    background: #e9ecef;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
                .hidden {
                    display: none;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔥 Glass Firing Curve Generator</h1>
                <p class="subtitle">Verktyg för Dalarnas Glasverkstad</p>
                
                <form id="curveForm">
                    <div class="form-group">
                        <label for="glassType">Vilken typ av glas ska du bränna?</label>
                        <select id="glassType" name="glassType" required>
                            <option value="">Välj glastyp...</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="ovenType">Vilken typ av ugn har du?</label>
                        <select id="ovenType" name="ovenType" required>
                            <option value="">Välj ugnstyp...</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="radius">Vilken är din största radie? (5, 10, 20, 30, 40, 50, 60)</label>
                        <select id="radius" name="radius" required>
                            <option value="">Välj radie...</option>
                            <option value="5">5</option>
                            <option value="10">10</option>
                            <option value="20">20</option>
                            <option value="30">30</option>
                            <option value="40">40</option>
                            <option value="50">50</option>
                            <option value="60">60</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="layers">Hur många lager har du som mest? (1-5)</label>
                        <select id="layers" name="layers" required>
                            <option value="">Välj antal lager...</option>
                            <option value="1">1</option>
                            <option value="2">2</option>
                            <option value="3">3</option>
                            <option value="4">4</option>
                            <option value="5">5</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="minutes">Hur många minuter vill du stanna på topptemperatur? (1-15)</label>
                        <select id="minutes" name="minutes" required>
                            <option value="">Välj minuter...</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="roomTemp">Vilken rumstemperatur har du i din verkstad? (10-30°C)</label>
                        <select id="roomTemp" name="roomTemp" required>
                            <option value="">Välj rumstemperatur...</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="firingType">Vilken bränning vill du ha?</label>
                        <select id="firingType" name="firingType" required>
                            <option value="">Välj bränningstyp...</option>
                            <option value="f">Fullfusing</option>
                            <option value="s">Slumping</option>
                            <option value="t">Tackfusing</option>
                        </select>
                    </div>

                    <button type="submit">Skapa Brännkurva</button>
                </form>
                
                <div id="result"></div>
            </div>

            <script>
                let glassData = {};

                // Load glass types when page loads
                document.addEventListener('DOMContentLoaded', function() {
                    loadGlassTypes();
                    populateSelectOptions();
                });

                function populateSelectOptions() {
                    // Populate minutes (1-15)
                    const minutesSelect = document.getElementById('minutes');
                    for (let i = 1; i <= 15; i++) {
                        minutesSelect.innerHTML += `<option value="${i}">${i}</option>`;
                    }

                    // Populate room temperature (10-30)
                    const roomTempSelect = document.getElementById('roomTemp');
                    for (let i = 10; i <= 30; i++) {
                        roomTempSelect.innerHTML += `<option value="${i}">${i}°C</option>`;
                    }
                }

                function loadGlassTypes() {
                    fetch('/api/glass-types')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            glassData = data.glass_data;
                            const select = document.getElementById('glassType');
                            data.glass_types.forEach((glass, index) => {
                                select.innerHTML += `<option value="${index}">${glass.namn}</option>`;
                            });
                        } else {
                            console.error('Failed to load glass types:', data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error loading glass types:', error);
                    });
                }

                // Update oven type options based on selected glass
                document.getElementById('glassType').addEventListener('change', function() {
                    const glassIndex = this.value;
                    const ovenSelect = document.getElementById('ovenType');
                    ovenSelect.innerHTML = '<option value="">Välj ugnstyp...</option>';

                    if (glassIndex !== '' && glassData.glass_types) {
                        const selectedGlass = glassData.glass_types[glassIndex];
                        
                        if (selectedGlass.kategori === 'floatglas') {
                            ovenSelect.innerHTML += '<option value="t">Toppvärmd</option>';
                        } else if (selectedGlass.kategori === 'COE-90/COE-96-glas') {
                            ovenSelect.innerHTML += '<option value="t">Toppvärmd</option>';
                            ovenSelect.innerHTML += '<option value="s">Sidovärmd</option>';
                        }
                    }
                });

                document.getElementById('curveForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const formData = new FormData(this);
                    const data = {};
                    for (let [key, value] of formData.entries()) {
                        data[key] = value;
                    }

                    document.getElementById('result').innerHTML = '<p class="loading">🔄 Skapar brännkurva...</p>';
                    
                    fetch('/api/create-curve', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            displayResults(data);
                        } else {
                            document.getElementById('result').innerHTML = 
                                `<div class="error">❌ Fel: ${data.error}</div>`;
                        }
                    })
                    .catch(error => {
                        document.getElementById('result').innerHTML = 
                            `<div class="error">❌ Fel: ${error.message}</div>`;
                    });
                });

                function displayResults(data) {
                    let phasesHtml = '';
                    data.phases.forEach(phase => {
                        phasesHtml += `
                            <div class="phase-info">
                                <h3>Fas ${phase.phase}</h3>
                                <p><strong>Start Temperatur:</strong> ${phase.start_temp}°C</p>
                                <p><strong>Slut Temperatur:</strong> ${phase.end_temp}°C</p>
                                <p><strong>Hastighet:</strong> ${phase.velocity}°C/h</p>
                                <p><strong>Hålltid:</strong> ${phase.holding_time} minuter</p>
                                <p><strong>Fasens tid:</strong> ${phase.time} minuter</p>
                            </div>
                        `;
                    });

                    const parametersHtml = `
                        <div class="parameter-info">
                            <strong>Parametrar:</strong><br>
                            Glastyp: ${data.glass_type}<br>
                            Bränningstyp: ${data.firing_type}<br>
                            Ugnstyp: ${data.parameters.oven_type}<br>
                            Radie: ${data.parameters.radius}<br>
                            Lager: ${data.parameters.layers}<br>
                            Minuter på topptemperatur: ${data.parameters.minutes}<br>
                            Rumstemperatur: ${data.parameters.room_temp}°C
                        </div>
                    `;

                    document.getElementById('result').innerHTML = `
                        <div class="success">✅ Brännkurva skapad framgångsrikt!</div>
                        ${parametersHtml}
                        <img src="data:image/png;base64,${data.plot}" alt="Brännkurva">
                        <h3>Total tid för programmet: ${data.total_time}</h3>
                        ${phasesHtml}
                    `;
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
        return jsonify({
            'success': True, 
            'glass_types': glass_types,
            'glass_data': handler.glass_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create-curve', methods=['POST'])
def create_firing_curve():
    """Create firing curve based on user input"""
    try:
        # Get user input from request
        data = request.get_json()
        
        # Load glass data
        with open('tables.json', 'r', encoding='utf-8') as file:
            glass_data = json.load(file)
        
        # Parse user input
        glass_index = int(data['glassType'])
        glass_info = glass_data["Glassorter"][glass_index]
        oven_type = data['ovenType']
        radius = int(data['radius'])
        layers = int(data['layers'])
        minutes = int(data['minutes'])
        room_temp = int(data['roomTemp'])
        firing_type = data['firingType']
        
        # Calculate temperatures based on firing type
        if firing_type == "f":
            topptemp = round((glass_info.get("f_topptemp")[0] + glass_info.get("f_topptemp")[1]) / 2)
        elif firing_type == "s":
            topptemp = round((glass_info.get("s_topptemp")[0] + glass_info.get("s_topptemp")[1]) / 2)
        elif firing_type == "t":
            topptemp = glass_info.get("t_topptemp")
        
        # Get timing tables based on glass category and oven type
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
        
        # Calculate velocities
        first_heating_velocity = int(999 if np.trunc(60*(inledande_smaltpunkt - room_temp)/uppvarmning_time) >= 999 else np.trunc(60*(inledande_smaltpunkt - room_temp)/uppvarmning_time))
        second_heating_velocity = int(999)
        first_cooling_velocity = int(np.trunc(60*(o_astemp - topptemp)/halltider_time))
        second_cooling_velocity = int(np.trunc(60*(n_astemp - o_astemp)/avspanning_time))
        last_cooling_velocity = int(-20)
        
        # Create the firing curve
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
        plt.style.use('default')  # Ensure clean styling
        
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
                    linewidth=3, markersize=8, label=f'Fas {idx+1}')
            
            # Update current temperature
            current_temp = phase._endTemp
        
        # Format the firing type for display
        firing_type_display = {
            'f': 'Fullfusing',
            's': 'Slumping', 
            't': 'Tackfusing'
        }
        
        plt.title(f'Brännkurva för {glass_info["namn"]} - {firing_type_display[firing_type]}', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Tid (minuter)', fontsize=14)
        plt.ylabel('Temperatur (°C)', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend(title='Faser', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        # Convert plot to base64 string
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=150)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        # Get phase information - ensure all values are JSON serializable
        phases = []
        for i in range(curve._totalPhases):
            phase = curve.findPhase(i)
            
            # Get color hex
            if phase._color is not None:
                color_hex = mcolors.to_hex(phase._color)
            else:
                color_hex = '#000000'
            
            phases.append({
                'phase': ensure_serializable(i + 1),
                'start_temp': ensure_serializable(phase._startTemp),
                'end_temp': ensure_serializable(phase._endTemp),
                'velocity': ensure_serializable(phase._velocity),
                'holding_time': ensure_serializable(phase._holdingTime),
                'time': ensure_serializable(phase._time),
                'color': color_hex
            })
        
        return jsonify({
            'success': True,
            'plot': plot_url,
            'phases': phases,
            'total_time': curve.getTotalTime(),
            'glass_type': glass_info["namn"],
            'firing_type': firing_type_display[firing_type],
            'parameters': {
                'radius': ensure_serializable(radius),
                'layers': ensure_serializable(layers),
                'minutes': ensure_serializable(minutes),
                'room_temp': ensure_serializable(room_temp),
                'oven_type': 'Toppvärmd' if oven_type == 't' else 'Sidovärmd'
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({'status': 'healthy', 'app': 'Glass Firing Curve Generator'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)