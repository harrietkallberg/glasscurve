from flask import Flask, render_template, request, jsonify, send_file
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from firing_curve import GlassTypeHandler
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/glass-types')
def get_glass_types():
    """Get available glass types"""
    try:
        handler = GlassTypeHandler('tables.json')
        glass_types = handler.glass_data["Glassorter"]
        return jsonify({'success': True, 'glass_types': glass_types})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create-curve', methods=['POST'])
def create_firing_curve():
    """Create firing curve based on user input"""
    try:
        data = request.json
        
        # Here you would process the user input and create the curve
        # For now, returning a simple response
        handler = GlassTypeHandler('tables.json')
        curve = handler.firing_curve_creator()
        
        # Generate plot
        plt.figure(figsize=(10, 6))
        
        total_time = 0
        current_temp = curve._roomTemp
        times = [0]
        temperatures = [current_temp]
        
        for idx, phase in enumerate(curve):
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

            plt.plot(time_points, temp_points, marker='o', label=f'Fas {idx+1}')
            current_temp = phase._endTemp

        plt.title('Brännkurva')
        plt.xlabel('Tid (minuter)')
        plt.ylabel('Temperatur (°C)')
        plt.grid(True)
        plt.legend()
        
        # Convert plot to base64 string
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        # Get phase information
        phases = []
        for i in range(curve._totalPhases):
            phase = curve.findPhase(i)
            phases.append({
                'phase': i + 1,
                'start_temp': phase._startTemp,
                'end_temp': phase._endTemp,
                'velocity': phase._velocity,
                'holding_time': phase._holdingTime,
                'time': phase._time
            })
        
        return jsonify({
            'success': True,
            'plot': plot_url,
            'phases': phases,
            'total_time': curve.getTotalTime()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)