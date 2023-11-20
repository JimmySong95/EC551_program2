# program description
# Overview
This project simulates the configuration and operation of a Field-Programmable Gate Array (FPGA) using Look-Up Tables (LUTs). It includes classes to model LUTs and the FPGA system, allowing for the assignment of logical functions, management of input and output connections, and calculation of resource allocations. The system is capable of generating a bitstream-like output representing the FPGA configuration.

# Features
LUT and FPGA Modeling: Classes to represent LUTs and the FPGA system.

Logical Function Assignment: Assign custom logical functions to each LUT.

Connection Management: Track and manage input and output connections of LUTs.

Bitstream Generation: Generate a structured string representing the FPGA's configuration.

Resource Allocation Calculation: Estimate the usage of LUTs and connections, and the memory requirements.

# Requirements
Python 3.x

# Usage
# 1.first edit input file: input.eqn. 

This system allows to input a list of logic expressions(in SOP form) to map to FPGA

if you want to handle independent SOP formula, you should edit the input.eqn file like this:
(A & B & ~C) | (~D & E & F) | (G & ~H)
(A & ~E & F) | (B & C & D & ~H)
(~A & ~B & C & D) | (E & ~F & G) | (H)

if you want to handle inter-independent SOP formula, you should edit the input.eqn file like this:
F1 = (A & B) | (~C & D) | (E & ~F)
F2 = (F1 & ~A) | (B & C & ~F1) | (~E & F)
F3 = (~F2 & D) | (A & ~B & E) | (F1 & ~C)

# 2.compile and run
The system using fpga_simulator.py to handle independent SOP and fpga_inter_dependent_simulation.py to handle inter-independent SOP

Open the file, Compile and run, then input following parameters:

num_luts = 100             // total number of LUTs
lut_type = 4               // number of inputs for LUTs
num_system_inputs = 6      // how many variables in your SOP
num_system_outputs = 4     // how many outputs in your SOP
