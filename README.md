 #Non blocking interactive 2-way communication GUI via PyQt.
 Perfect, you are here. So you are probably struggling just as I have had. Carry on, feedbacks welcomed!
 ## Idea
 I was not happy with native Arduino Serial Plotter, nor was I keen on using Processing. Not that its not a good tool, I just wanted to stick to pure python. 
 There are countless tutorials online, which helpled me put together this GUI for serial communication + visualizer. 
 However, most of those projects are not covering at least one of the following:
 - threading (GUI + serial on separate threads)
 - multi plotting (having more than one plot active)
 - sending and receiving via GUI (plotting)
 - modular approach
 
 Therefore I decided to make something on my own, to accelerate my own projects.
 If you need some quick solution to visualize serial data from Arduino, then this is a perfect GUI for you.
 If you need a good basis to begin with, to create much better and powerful GUI, then please reuse what I have created. 
 
 ## Overview
 Communication is split in 2 sides. PC (refered as Python side) and Arduino side. 
 ### Python side
 GUI is very simple to use. You specify basic things like COM Port, Baud rate. However in this app, you also need to specify the type of data your Arduino/Teensy/STM/AnyOtherDevice is sending. 
 You can choose between:
 - 2 bytes (for integer)
 - 4 bytes (for floats)
 - 8 bytes (for doubles)
 For more refere to implementation.
 
 
 ### Arduino side
 Complete implementation required to be flashed on your device is more or less covered in 50 lines. Everything is documented and modular approach is used. Please refer to Arduino code (.ino). 
 
 ## Functionality
 There are 2 main parts. Sending and receiving. 
 ### Rx
 For receving, at the moment you can only plot the data. However the plotter is incredibly powerful, as it is done with PyQt. It is incredibly easy to use. 
 Main features which are implemented, but not covered in native Arduino serial plotter:
 - you can stop the plot
 - you can export the plot
 - trigger for plot (a bit buggy)
 
 ### Tx
 Transmission works more or less the same way as in native Arduino. However I wanted to extend it, to match the SerialRead custom function in the Arduino code. 
 Basic idea is to write the "identifier" and "value". Where identifier tells Arduino "how to clasify data" and "value" tells, well the value. 
 Example: Pin13:1 tells arduino to turn on the Pin13 (where Led resides).
 
 Please note, that this works similar but that it is not Firmata! The "Pin13" functionality is my custom implementation (please see Arduino code). 
 I wanted to keep it simple and keep complete functionality of Arduino (because when you flash Firmata, Arduino becomes "dumb". Basically you turn it into BoB.
 
 
![alt text](https://github.com/aljazjelen/PyArduinoSerial/blob/main/frontImage.png?raw=true)