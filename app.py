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
    except:
        # If template doesn't exist, return a simple HTML page
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Glass Firing Curve Generator</title>
        </head>
        <body>
            <h1>Glass Firing Curve Generator</h1>
            <p>Welcome to the Glass Firing Curve Generator!</p>
            <button onclick="createCurve()">Generate Sample Curve</button>
            <div id="result"></div>
            
            <script>
            function createCurve() {
                fetch('/api/create-curve', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        document.getElementById('result').innerHTML = 
                            '<h2>Curve Generated!</h2><img src="data:image/png;base64,' + data.plot + '">';
                    } else {
                        document.getElementById('result').innerHTML = 'Error: ' + data.error;
                    }
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
    """Create firing curve based on user parameters"""
    try:
        # Use the existing automated curve creation
        handler = GlassTypeHandler('tables.json')
        curve = handler.firing_curve_creator()
        
        # Generate plot
        total_time = 0
        current_temp = curve._roomTemp
        
        plt.figure(figsize=(12, 8))
        
        # Create a colormap
        cmap = plt.get_cmap('tab20')
        
        times = [0]
        temperatures = [current_temp]
        
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
            
            # Append to lists for potential use later
            times.append(end_time)
            temperatures.append(current_temp)
        
        plt.title('Brännkurva för Glasverkstad', fontsize=16, fontweight='bold')
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
            'total_time': curve.getTotalTime()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({'status': 'healthy', 'app': 'Glass Firing Curve Generator'})

if __name__ == '__main__':
    # CRITICAL: Use Railway's PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    # CRITICAL: Bind to 0.0.0.0 for Railway
    app.run(host='0.0.0.0', port=port, debug=False)