# Firing Curve Simulator
### Overview
This module simulates a firing curve for glass-making processes. It provides comprehensive management of temperature phases, enabling setting, updating, and removing phases as part of the curve. The system calculates the total time for the curve based on the durations of all phases.

<div align="center">
  <img src="firing_curves.webp" alt="The Art of Firing Curves" width="400">
  <br>
  <figcaption>The Art of Firing Curves - a detailed view.</figcaption>
</div>

# Features
### Add New Phases
Insert a new phase specifying velocity, end temperature, and holding time. Phases can be added at any specified or default end position within the curve.

### Modify Phases
Update the velocity, end temperature, or holding time of any phase in the curve.

### Delete Phases
Remove a phase from the curve based on its index.

# Requirements
Python 3.6 or later NumPy library
### Installation
Ensure that Python and NumPy are installed on your system. You can install NumPy using pip:  pip install numpy 

### Usage
Import firing_curves.py and create an instance of the firingCurve class. Use the following methods to manage the firing curve:

* newPhase(velocity=1, endTemp=0, holdingTime=0, index=None)   
Purpose: Adds a new phase to the firing curve.    
velocity: The rate at which the temperature changes.    
endTemp: The target temperature for the phase.  
holdingTime: Duration to hold the temperature once reached.  
index: Position in the list where the phase is inserted; appends at the end if not specified.  
* changePhaseEndTemp(index, newEndTemp)  
Purpose: Modifies the end temperature of an existing phase.  
index: Index of the phase to modify.  
newEndTemp: New target end temperature.   
* changePhaseVelocity(index, newVelocity)   
Purpose: Adjusts the velocity of a specified phase.   
index: Index of the phase to modify.   
newVelocity: New velocity rate.   
* changePhaseHoldingTime(index, newHoldingTime)   
Purpose: Changes the holding time for a specified phase.   
index: Index of the phase to modify.   
newHoldingTime: New holding time duration.   
* removePhase(index)   
Purpose: Removes a phase from the firing curve.   
index: Index of the phase to be removed.   
* findPhase(index)   
Purpose: Retrieves a phase by its index.   
index: Index of the phase to find.   
* _healthy()   
Purpose: Performs a health check to validate the internal structure and time calculations of the curve.

# Example
### Old example:
from firing_curves.py import firingCurve 

fc = firingCurve(roomTemp=20)  
fc.newPhase(100, 500, 30)  
fc.changePhaseVelocity(0, 120)  
fc.changePhaseHoldingTime(0, 20)  
fc.changePhaseEndTemp(0, 550)  
fc.removePhase(0)  

### New example:
The code now lets the user input information about the glass, oven and other parameters relevant to the firing curve. 
The code takes if from there based on data in the json-file.
 
### Development
Modify and expand the module by editing the Python script. Ensure that any changes maintain the integrity of the firing curve's linked list structure.

### Testing
The main function included at the end of the module serves as a basic test suite for the functionality of the firing curve management system. Adjust the test cases to suit changes and enhancements to the module functionality.
