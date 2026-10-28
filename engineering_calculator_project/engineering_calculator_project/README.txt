ENGINEERING WORKBENCH

Requirements:
  Python 3.10 or newer recommended
  Tkinter (included with standard Python on Windows)

Install dependencies in VS Code terminal:
  py -m pip install -r requirements.txt

Run:
  py engineering_calculator.py

Tabs included:
  Scientific, Calculus, Numerical Methods, Matrices & Vectors, Statistics,
  Engineering Units, Electrical, Mechanics, Signals, Number Systems, History.

Important notes:
- This is a broad extensible engineering workbench, not a guarantee of every
  specialized formula in every engineering discipline.
- Enter expressions such as sin(30), sqrt(2), log(100), 2^10, factorial(5).
- Angle mode applies to the scientific calculator trig functions. The numerical
  method and symbolic calculus inputs use their libraries' standard conventions.
- Unit conversion inputs must use consistent units and are educational tools;
  verify safety-critical or design calculations independently.
- Euler ODE tab currently integrates y'=f(x), y(a)=0, not general y'=f(x,y).
- Signal low-pass filter uses an automatically selected cutoff; customize before
  using it for actual signal-design work.
