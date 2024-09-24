# Configuration of stepper motor controller
Our shakebot has configuration of the stepper motor controller as follows.

## Pulse/rev ratio
By defautl, we set the pulse/rev ratio as 10000:

| SW1  | SW2  | SW3  | SW4  |
|------|------|------|------|
| OFF  | ON   | OFF  | OFF  |


## Mode setting 
| SW5 | SW6 | SW7 | SW8 | SW9 |
|-----|-----|-----|-----|-----|
| OFF | OFF | ON  | OFF | OFF |


SW6: OFF for NEMA 34; ON for NEMA 23.  
SW7: fully closed loop to use the encoder.  
SW9: shorter filter time to have faster response.  
