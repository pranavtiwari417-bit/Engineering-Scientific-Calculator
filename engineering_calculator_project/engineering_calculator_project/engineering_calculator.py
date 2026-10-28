"""Engineering Workbench — extensible engineering/scientific calculator.
Requires: numpy, scipy, sympy, matplotlib
Run: python engineering_calculator.py
"""
import ast, math, cmath, operator, random, statistics, tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import sympy as sp
from scipy import integrate, optimize, stats, signal, fft

APP_BG = "#101522"
PANEL = "#1B2335"
BTN = "#2B3852"
ACCENT = "#168C9D"
GREEN = "#18A999"
FG = "#F4F7FF"
MUTED = "#AAB6D0"

x, y, z, t = sp.symbols("x y z t")
ANGLE_MODE = "DEG"

# ---------- Expression evaluator (AST allowlist; no arbitrary Python execution) ----------
def _trig(fn):
    return lambda v: fn(math.radians(v) if ANGLE_MODE == "DEG" else v)
def _invtrig(fn):
    return lambda v: math.degrees(fn(v)) if ANGLE_MODE == "DEG" else fn(v)
def _factorial(v):
    if not isinstance(v, (int, float, np.integer, np.floating)) or not float(v).is_integer() or v < 0 or v > 170:
        raise ValueError("Factorial needs an integer from 0 to 170")
    return math.factorial(int(v))
def _root(v, n=2):
    if n == 0: raise ValueError("Root degree cannot be zero")
    if v < 0 and float(n).is_integer() and int(n) % 2:
        return -((-v) ** (1 / n))
    return v ** (1 / n)
def _sinc(v): return 1.0 if v == 0 else math.sin(v) / v

def math_namespace(ans=0):
    return {
        "pi": math.pi, "e": math.e, "tau": math.tau, "ans": ans,
        "sin": _trig(math.sin), "cos": _trig(math.cos), "tan": _trig(math.tan),
        "asin": _invtrig(math.asin), "acos": _invtrig(math.acos), "atan": _invtrig(math.atan),
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "asinh": math.asinh, "acosh": math.acosh, "atanh": math.atanh,
        "sqrt": math.sqrt, "cbrt": lambda v: math.copysign(abs(v)**(1/3), v), "root": _root,
        "exp": math.exp, "log": math.log10, "ln": math.log, "log2": math.log2,
        "logn": lambda v, base: math.log(v, base), "abs": abs, "floor": math.floor,
        "ceil": math.ceil, "round": round, "trunc": math.trunc, "factorial": _factorial,
        "gamma": math.gamma, "erf": math.erf, "erfc": math.erfc, "sinc": _sinc,
        "hypot": math.hypot, "degrees": math.degrees, "radians": math.radians,
        "comb": math.comb, "perm": math.perm, "gcd": math.gcd, "lcm": math.lcm,
        "min": min, "max": max, "sum": sum, "mean": statistics.mean,
        "median": statistics.median, "stdev": statistics.stdev, "variance": statistics.variance,
        "rand": random.random, "real": lambda v: complex(v).real, "imag": lambda v: complex(v).imag,
        "conj": lambda v: complex(v).conjugate(), "phase": cmath.phase,
        "sind": lambda v: math.sin(math.radians(v)), "cosd": lambda v: math.cos(math.radians(v)),
        "tand": lambda v: math.tan(math.radians(v)),
        "sinr": math.sin, "cosr": math.cos, "tanr": math.tan,
        "cot": lambda v: 1/_trig(math.tan)(v), "sec": lambda v: 1/_trig(math.cos)(v),
        "csc": lambda v: 1/_trig(math.sin)(v),
    }

_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
           ast.Mod: operator.mod, ast.Pow: operator.pow}
_UNOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
def calculate_expression(expr, ans=0):
    expr = expr.strip().replace("×", "*").replace("÷", "/").replace("π", "pi").replace("^", "**")
    if not expr: raise ValueError("Enter an expression")
    if len(expr) > 1000: raise ValueError("Expression is too long")
    tree = ast.parse(expr, mode="eval")
    ns = math_namespace(ans)
    def check(n):
        if isinstance(n, ast.Expression): check(n.body)
        elif isinstance(n, ast.Constant):
            if type(n.value) not in (int, float, complex): raise ValueError("Only numeric constants are allowed")
        elif isinstance(n, ast.Name):
            if n.id not in ns: raise ValueError(f"Unknown name: {n.id}")
        elif isinstance(n, ast.BinOp) and type(n.op) in _BINOPS:
            check(n.left); check(n.right)
        elif isinstance(n, ast.UnaryOp) and type(n.op) in _UNOPS: check(n.operand)
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            if n.func.id not in ns or n.keywords: raise ValueError("Unsupported function call")
            if len(n.args) > 100: raise ValueError("Too many arguments")
            for a in n.args: check(a)
        else: raise ValueError("Unsupported expression syntax")
    check(tree)
    result = eval(compile(tree, "<calculator>", "eval"), {"__builtins__": {}}, ns)
    if isinstance(result, (float, np.floating)) and not math.isfinite(float(result)):
        raise ValueError("Result is not finite")
    if isinstance(result, complex) and (not math.isfinite(result.real) or not math.isfinite(result.imag)):
        raise ValueError("Result is not finite")
    if isinstance(result, int) and result.bit_length() > 100000: raise ValueError("Result too large")
    return result

# ---------- UI helpers ----------
class EngineeringWorkbench:
    def __init__(self, root):
        self.root = root
        self.root.title("Engineering Workbench | Scientific Calculator")
        self.root.geometry("1220x850")
        self.root.minsize(980, 680)
        self.root.configure(bg=APP_BG)
        self.ans = 0
        self.memory = 0
        self.history = []
        self._style()
        header = tk.Frame(root, bg=APP_BG); header.pack(fill="x", padx=18, pady=12)
        tk.Label(header, text="ENGINEERING WORKBENCH", bg=APP_BG, fg=FG,
                 font=("Segoe UI", 21, "bold")).pack(side="left")
        self.angle_btn = tk.Button(header, text="ANGLE: DEG", command=self.toggle_angle,
                                    bg=ACCENT, fg="white", relief="flat", padx=12, pady=8)
        self.angle_btn.pack(side="right")
        self.notebook = ttk.Notebook(root); self.notebook.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self.tabs = {}
        for name in ["Scientific", "Calculus", "Numerical Methods", "Matrices & Vectors", "Statistics", "Engineering Units", "Electrical", "Mechanics", "Signals", "Number Systems", "History"]:
            frame = tk.Frame(self.notebook, bg=APP_BG)
            self.notebook.add(frame, text=name); self.tabs[name] = frame
        self.build_scientific(); self.build_calculus(); self.build_numerical(); self.build_matrices()
        self.build_statistics(); self.build_units(); self.build_electrical(); self.build_mechanics()
        self.build_signals(); self.build_bases(); self.build_history()

    def _style(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TNotebook", background=APP_BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=PANEL, foreground=FG, padding=(10,8), font=("Segoe UI",9,"bold"))
        s.map("TNotebook.Tab", background=[("selected", ACCENT)])
        s.configure("TCombobox", fieldbackground=PANEL, background=PANEL, foreground=FG)

    def toggle_angle(self):
        global ANGLE_MODE
        ANGLE_MODE = "RAD" if ANGLE_MODE == "DEG" else "DEG"
        self.angle_btn.config(text=f"ANGLE: {ANGLE_MODE}")

    def label(self, parent, text):
        tk.Label(parent, text=text, bg=APP_BG, fg=FG, font=("Segoe UI",10,"bold")).pack(anchor="w", padx=12, pady=(9,3))
    def entry(self, parent, default=""):
        e = tk.Entry(parent, bg=PANEL, fg=FG, insertbackground=FG, relief="flat", font=("Consolas",12))
        e.pack(fill="x", padx=12, pady=4, ipady=7)
        if default: e.insert(0, default)
        return e
    def output(self, parent, height=6):
        o = tk.Text(parent, height=height, bg=PANEL, fg=GREEN, insertbackground=FG,
                    relief="flat", font=("Consolas",10), wrap="word")
        o.pack(fill="both", expand=True, padx=12, pady=8); return o
    def show(self, widget, text):
        widget.configure(state="normal"); widget.delete("1.0","end"); widget.insert("end",str(text))
    def button(self, parent, text, command, color=ACCENT):
        tk.Button(parent,text=text,command=command,bg=color,fg="white",relief="flat",
                  activebackground=GREEN,font=("Segoe UI",9,"bold"),padx=8,pady=7).pack(side="left", padx=3, pady=3)
    def run_guarded(self, out, fn):
        try:
            result = fn(); self.show(out, result)
            self.history.append(f"{result}"); self.refresh_history()
        except Exception as exc: self.show(out, f"Error: {exc}")
    def parse_numbers(self, entry): return [float(q.strip()) for q in entry.get().split(",") if q.strip()]

    # Scientific calculator
    def build_scientific(self):
        f=self.tabs["Scientific"]; self.label(f,"Expression — use sin(30), log(100), 2^10, factorial(5), comb(8,3), ans")
        self.expr=self.entry(f,"sin(30)+sqrt(144)+log(100)"); self.expr.bind("<Return>",lambda e:self.do_calc()); self.expr.bind("<Escape>",lambda e:self.expr.delete(0,"end"))
        pad=tk.Frame(f,bg=APP_BG); pad.pack(fill="x",padx=8,pady=4)
        keys=["7","8","9","÷","sin(","cos(","tan(","asin(","4","5","6","×","sqrt(","cbrt(","log(","ln(","1","2","3","−","(",")","pi","e","0",".","^","+","factorial(","abs(","ans","AC"]
        for i,k in enumerate(keys):
            color=GREEN if k=="AC" else (ACCENT if k in ["÷","×","−","+","^"] else BTN)
            tk.Button(pad,text=k,bg=color,fg=FG,relief="flat",font=("Segoe UI",10,"bold"),
                      command=lambda q=k:self.calc_key(q),pady=8).grid(row=i//8,column=i%8,sticky="nsew",padx=2,pady=2)
        for c in range(8): pad.columnconfigure(c,weight=1)
        row=tk.Frame(f,bg=APP_BG); row.pack(fill="x",padx=8)
        for name,fn in [("Calculate",self.do_calc),("Clear",lambda:self.expr.delete(0,"end")),("M+",self.mem_add),("MR",self.mem_recall),("MC",self.mem_clear)]: self.button(row,name,fn)
        self.calc_out=self.output(f,5)
    def calc_key(self,k):
        if k=="AC": self.expr.delete(0,"end")
        else: self.expr.insert(tk.INSERT, {"÷":"/","×":"*","−":"-"}.get(k,k))
    def do_calc(self):
        def op():
            self.ans=calculate_expression(self.expr.get(),self.ans)
            return f"Result: {self.ans}\nAngle mode: {ANGLE_MODE}\nMemory: {self.memory}"
        self.run_guarded(self.calc_out,op)
    def mem_add(self):
        try:self.memory+=float(self.ans); self.show(self.calc_out,f"Memory = {self.memory}")
        except Exception as e:self.show(self.calc_out,f"Memory error: {e}")
    def mem_recall(self): self.expr.insert(tk.INSERT,str(self.memory))
    def mem_clear(self): self.memory=0; self.show(self.calc_out,"Memory cleared")

    # Calculus symbolic
    def build_calculus(self):
        f=self.tabs["Calculus"]; self.label(f,"Expression in x (SymPy syntax: sin(x), exp(x), log(x), x**2)")
        self.cexpr=self.entry(f,"x**3-2*x+1"); self.label(f,"Point / lower limit"); self.ca=self.entry(f,"1"); self.label(f,"Upper limit"); self.cb=self.entry(f,"3")
        bar=tk.Frame(f,bg=APP_BG); bar.pack(fill="x",padx=8,pady=5)
        ops=[("Derivative",lambda:sp.diff(self.symexpr(),x)),("2nd derivative",lambda:sp.diff(self.symexpr(),x,2)),
             ("Antiderivative",lambda:sp.integrate(self.symexpr(),x)),("Definite integral",lambda:sp.integrate(self.symexpr(),(x,float(self.ca.get()),float(self.cb.get())))),
             ("Limit",lambda:sp.limit(self.symexpr(),x,float(self.ca.get()))),("Taylor series",lambda:sp.series(self.symexpr(),x,float(self.ca.get()),7)),
             ("Evaluate",lambda:sp.N(self.symexpr().subs(x,float(self.ca.get())))),("Simplify",lambda:sp.simplify(self.symexpr())),
             ("Factor",lambda:sp.factor(self.symexpr())),("Solve = 0",lambda:sp.solve(self.symexpr(),x))]
        for n,fn in ops:self.button(bar,n,lambda fn=fn:self.run_guarded(self.cout,fn))
        self.cout=self.output(f,10)
    def symexpr(self): return sp.sympify(self.cexpr.get())

    # Numerical methods
    def build_numerical(self):
        f=self.tabs["Numerical Methods"]; self.label(f,"f(x) for numerical methods (NumPy syntax: x**3-x-2, sin(x), exp(x))")
        self.nexpr=self.entry(f,"x**3-x-2"); self.label(f,"Initial guess / a"); self.na=self.entry(f,"1.5"); self.label(f,"b / second guess"); self.nb=self.entry(f,"2")
        self.label(f,"Integration upper bound / step count"); self.nc=self.entry(f,"1000")
        bar=tk.Frame(f,bg=APP_BG); bar.pack(fill="x",padx=8,pady=5)
        for n,fn in [("Bisection",self.bisection),("Newton root",self.newton_root),("Secant root",self.secant_root),
                     ("Brent root",self.brent_root),("Numerical derivative",self.num_derivative),("Definite integral",self.num_integral),
                     ("Euler ODE y'=f(x)",self.euler_ode)]: self.button(bar,n,lambda fn=fn:self.run_guarded(self.nout,fn))
        self.nout=self.output(f,10)
    def npfunc(self):
        src=self.nexpr.get().replace("^","**")
        allowed={"sin":np.sin,"cos":np.cos,"tan":np.tan,"exp":np.exp,"log":np.log,"sqrt":np.sqrt,"abs":np.abs,"pi":np.pi}
        # Only intended math names and x are supplied; builtins are removed.
        code=compile(ast.parse(src,mode="eval"),"<numeric function>","eval")
        for node in ast.walk(ast.parse(src,mode="eval")):
            if isinstance(node,ast.Name) and node.id not in set(allowed)|{"x"}: raise ValueError(f"Unknown name {node.id}")
            if isinstance(node,(ast.Attribute,ast.Subscript,ast.Lambda,ast.DictComp,ast.ListComp)): raise ValueError("Unsupported syntax")
        return lambda value: float(eval(code,{"__builtins__":{}},dict(allowed,x=value)))
    def bisection(self):
        fn=self.npfunc(); a=float(self.na.get()); b=float(self.nb.get())
        return f"Root = {optimize.bisect(fn,a,b)}"
    def newton_root(self): return f"Root = {optimize.newton(self.npfunc(),float(self.na.get()))}"
    def secant_root(self): return f"Root = {optimize.root_scalar(self.npfunc(),x0=float(self.na.get()),x1=float(self.nb.get()),method='secant').root}"
    def brent_root(self): return f"Root = {optimize.brentq(self.npfunc(),float(self.na.get()),float(self.nb.get()))}"
    def num_derivative(self):
        fn=self.npfunc(); a=float(self.na.get()); h=1e-5
        return f"Central derivative at x={a}: {(fn(a+h)-fn(a-h))/(2*h)}"
    def num_integral(self): return f"Integral = {integrate.quad(self.npfunc(),float(self.na.get()),float(self.nb.get()))[0]}"
    def euler_ode(self):
        # For a general ODE enter f(x) in the field; integrates y'=f(x), y(a)=0.
        fn=self.npfunc(); a=float(self.na.get()); b=float(self.nb.get()); steps=max(2,min(100000,int(float(self.nc.get())))); h=(b-a)/steps; yy=0.0; xx=a
        for _ in range(steps): yy += h*fn(xx); xx += h
        return f"Euler approximation for y'=f(x), y({a})=0 at x={b}: y≈{yy}\nSteps={steps}; h={h}"

    # Matrices and vectors
    def build_matrices(self):
        f=self.tabs["Matrices & Vectors"]; self.label(f,"Matrix A and B: nested list syntax, e.g. [[1,2],[3,4]]")
        self.ma=self.entry(f,"[[1,2],[3,4]]"); self.mb=self.entry(f,"[[5,6],[7,8]]")
        bar=tk.Frame(f,bg=APP_BG);bar.pack(fill="x",padx=8,pady=5)
        ops=[("A+B",lambda a,b:a+b),("A-B",lambda a,b:a-b),("A×B",lambda a,b:a@b),("A elementwise B",lambda a,b:a*b),
             ("det(A)",lambda a,b:np.linalg.det(a)),("inv(A)",lambda a,b:np.linalg.inv(a)),("transpose(A)",lambda a,b:a.T),
             ("rank(A)",lambda a,b:np.linalg.matrix_rank(a)),("eigenvalues/vectors",lambda a,b:np.linalg.eig(a)),
             ("SVD(A)",lambda a,b:np.linalg.svd(a)),("condition number",lambda a,b:np.linalg.cond(a)),
             ("least squares A·x≈b",lambda a,b:np.linalg.lstsq(a,b,rcond=None))]
        for n,fn in ops:self.button(bar,n,lambda fn=fn:self.run_guarded(self.mout,lambda:fn(self.matrix(self.ma),self.matrix(self.mb))))
        self.label(f,"Vector A and B: comma-separated numbers");self.va=self.entry(f,"1,2,3");self.vb=self.entry(f,"4,5,6")
        bar2=tk.Frame(f,bg=APP_BG);bar2.pack(fill="x",padx=8,pady=5)
        for n,fn in [("Dot",lambda a,b:np.dot(a,b)),("Cross",lambda a,b:np.cross(a,b)),("Norm A",lambda a,b:np.linalg.norm(a)),("Normalize A",lambda a,b:a/np.linalg.norm(a))]:
            self.button(bar2,n,lambda fn=fn:self.run_guarded(self.mout,lambda:fn(np.array(self.parse_numbers(self.va)),np.array(self.parse_numbers(self.vb)))))
        self.mout=self.output(f,10)
    def matrix(self,e):
        val=ast.literal_eval(e.get()); a=np.array(val,dtype=float)
        if a.ndim!=2: raise ValueError("Matrix must be 2D")
        return a

    # Statistics
    def build_statistics(self):
        f=self.tabs["Statistics"];self.label(f,"Data values separated by commas");self.data=self.entry(f,"12,15,17,19,22,24,24,28,31")
        bar=tk.Frame(f,bg=APP_BG);bar.pack(fill="x",padx=8,pady=5)
        funcs=[("Count",lambda d:len(d)),("Mean",np.mean),("Median",np.median),("Mode",lambda d:statistics.multimode(d)),
               ("Min / Max",lambda d:(np.min(d),np.max(d))),("Range",np.ptp),("Sample variance",lambda d:np.var(d,ddof=1)),
               ("Sample std dev",lambda d:np.std(d,ddof=1)),("Quartiles",lambda d:np.percentile(d,[25,50,75])),
               ("IQR",lambda d:np.percentile(d,75)-np.percentile(d,25)),("Skewness",stats.skew),("Kurtosis",stats.kurtosis)]
        for n,fn in funcs:self.button(bar,n,lambda fn=fn:self.run_guarded(self.sout,lambda:fn(np.array(self.parse_numbers(self.data),dtype=float))))
        self.label(f,"Distribution: choose Normal / Binomial / Poisson"); self.dist=ttk.Combobox(f,values=["Normal","Binomial","Poisson"],state="readonly");self.dist.pack(anchor="w",padx=12);self.dist.set("Normal")
        self.label(f,"Parameters: Normal = mean,sd,x | Binomial = n,p,k | Poisson = lambda,k");self.dp=self.entry(f,"0,1,1.96")
        self.button(f,"Calculate PDF/PMF and CDF",self.distribution)
        self.sout=self.output(f,8)
    def distribution(self):
        def op():
            a=self.parse_numbers(self.dp); typ=self.dist.get()
            if typ=="Normal":
                mu,sd,q=a
                if sd<=0:raise ValueError("Standard deviation must be positive")
                return f"PDF={stats.norm.pdf(q,mu,sd)}\nCDF={stats.norm.cdf(q,mu,sd)}\nP(X>q)={stats.norm.sf(q,mu,sd)}"
            if typ=="Binomial":
                n,p,k=a;return f"PMF={stats.binom.pmf(k,int(n),p)}\nCDF={stats.binom.cdf(k,int(n),p)}"
            lam,k=a;return f"PMF={stats.poisson.pmf(k,lam)}\nCDF={stats.poisson.cdf(k,lam)}"
        self.run_guarded(self.sout,op)

    # Units: explicit conversions
    def build_units(self):
        f=self.tabs["Engineering Units"];self.label(f,"Input value");self.uv=self.entry(f,"1")
        self.label(f,"Conversion");self.uc=ttk.Combobox(f,state="readonly",values=list(self.unit_functions().keys()));self.uc.pack(fill="x",padx=12,pady=5);self.uc.current(0)
        self.button(f,"Convert",lambda:self.run_guarded(self.uout,lambda:f"{self.uv.get()} {self.uc.get()} = {self.unit_functions()[self.uc.get()](float(self.uv.get())):.12g}"))
        self.label(f,"Supported conversions include length, area, volume, mass, time, speed, force, pressure, energy, power, temperature, electrical units and SI prefixes.")
        self.uout=self.output(f,7)
    def unit_functions(self):
        return {
          "m → ft":lambda v:v*3.280839895,"ft → m":lambda v:v/3.280839895,"km → mile":lambda v:v*.621371192,"mile → km":lambda v:v/ .621371192,
          "cm → inch":lambda v:v/2.54,"inch → cm":lambda v:v*2.54,"mm → inch":lambda v:v/25.4,"inch → mm":lambda v:v*25.4,
          "m² → ft²":lambda v:v*10.7639104,"ft² → m²":lambda v:v/10.7639104,"L → m³":lambda v:v/1000,"m³ → L":lambda v:v*1000,
          "kg → lb":lambda v:v*2.20462262,"lb → kg":lambda v:v/2.20462262,"g → kg":lambda v:v/1000,"tonne → kg":lambda v:v*1000,
          "min → s":lambda v:v*60,"hour → s":lambda v:v*3600,"day → s":lambda v:v*86400,"km/h → m/s":lambda v:v/3.6,"m/s → km/h":lambda v:v*3.6,
          "N → lbf":lambda v:v*.224808943,"lbf → N":lambda v:v/.224808943,"Pa → psi":lambda v:v/6894.757293,"psi → Pa":lambda v:v*6894.757293,
          "bar → Pa":lambda v:v*1e5,"kPa → Pa":lambda v:v*1e3,"MPa → Pa":lambda v:v*1e6,"GPa → Pa":lambda v:v*1e9,
          "J → cal":lambda v:v/4.184,"cal → J":lambda v:v*4.184,"kWh → J":lambda v:v*3.6e6,"W → hp":lambda v:v/745.699872,"hp → W":lambda v:v*745.699872,
          "kW → W":lambda v:v*1e3,"MW → W":lambda v:v*1e6,"C → F":lambda v:v*9/5+32,"F → C":lambda v:(v-32)*5/9,"C → K":lambda v:v+273.15,"K → C":lambda v:v-273.15,
          "mA → A":lambda v:v/1000,"A → mA":lambda v:v*1000,"kA → A":lambda v:v*1000,"kΩ → Ω":lambda v:v*1000,"MΩ → Ω":lambda v:v*1e6,
          "μF → F":lambda v:v*1e-6,"nF → F":lambda v:v*1e-9,"pF → F":lambda v:v*1e-12,"mH → H":lambda v:v*1e-3,"μH → H":lambda v:v*1e-6,
          "bar → atm":lambda v:v/1.01325,"atm → Pa":lambda v:v*101325,"L/min → m³/s":lambda v:v/60000,"rpm → rad/s":lambda v:v*2*math.pi/60,
        }

    # Electrical engineering
    def build_electrical(self):
        f=self.tabs["Electrical"];self.label(f,"Choose calculator");self.ec=ttk.Combobox(f,state="readonly",values=["Ohm's law: V=I·R","Power: P=V·I","Series resistors","Parallel resistors","Capacitive reactance","Inductive reactance","Series RLC impedance","Voltage divider","Decibels: 10log10(P2/P1)"]);self.ec.pack(fill="x",padx=12,pady=5);self.ec.current(0)
        self.label(f,"Inputs (comma-separated; see examples below)");self.ein=self.entry(f,"12,2")
        self.label(f,"Examples: Ohm V: I,R | P: V,I | series/parallel: R1,R2,... | Xc: f,C | Xl: f,L | RLC: R,f,L,C | divider: Vin,R1,R2 | dB: P2,P1")
        self.button(f,"Calculate",self.electrical_calc);self.eout=self.output(f,10)
    def electrical_calc(self):
        def op():
            q=self.parse_numbers(self.ein);typ=self.ec.get()
            if typ.startswith("Ohm"): i,r=q;return f"V = I·R = {i*r} V"
            if typ.startswith("Power"): v,i=q;return f"P = V·I = {v*i} W\nR=V/I = {v/i if i else 'undefined'} Ω"
            if typ=="Series resistors":return f"Rtotal = {sum(q)} Ω"
            if typ=="Parallel resistors":
                if any(v==0 for v in q):raise ValueError("Resistance cannot be zero")
                return f"Rtotal = {1/sum(1/v for v in q)} Ω"
            if typ.startswith("Capacitive"): f,c=q;return f"Xc = 1/(2πfC) = {1/(2*math.pi*f*c)} Ω"
            if typ.startswith("Inductive"): f,l=q;return f"Xl = 2πfL = {2*math.pi*f*l} Ω"
            if typ.startswith("Series RLC"):
                r,f,l,c=q;xl=2*math.pi*f*l;xc=1/(2*math.pi*f*c);return f"XL={xl} Ω\nXC={xc} Ω\nZ={complex(r,xl-xc)} Ω\n|Z|={abs(complex(r,xl-xc))} Ω\nPhase={math.degrees(math.atan2(xl-xc,r))}°"
            if typ.startswith("Voltage divider"):vin,r1,r2=q;return f"Vout = Vin·R2/(R1+R2) = {vin*r2/(r1+r2)} V"
            p2,p1=q
            if p1<=0 or p2<=0:raise ValueError("Powers must be positive")
            return f"Gain = {10*math.log10(p2/p1)} dB"
        self.run_guarded(self.eout,op)

    # Mechanics and basic physics
    def build_mechanics(self):
        f=self.tabs["Mechanics"];self.label(f,"Select formula");self.mc=ttk.Combobox(f,state="readonly",values=["Kinematics: v=u+at; s=ut+½at²","Projectile range","Newton: F=m·a","Weight: W=m·g","Density: rho=m/V","Pressure: P=F/A","Work: W=F·d·cos(theta)","Kinetic energy","Potential energy","Spring force","Stress and strain","Beam simply-supported central load: Mmax=PL/4"]);self.mc.pack(fill="x",padx=12,pady=5);self.mc.current(0)
        self.label(f,"Inputs (comma-separated; units must be consistent)");self.minp=self.entry(f,"u,a,t")
        self.label(f,"Input examples: kinematics u,a,t | projectile u,angle_deg,g | F=m*a m,a | weight m,g | density m,V | pressure F,A | work F,d,angle_deg | KE m,v | PE m,g,h | spring k,x | stress force,area | beam P,L")
        self.button(f,"Calculate",self.mechanics_calc);self.mechout=self.output(f,10)
    def mechanics_calc(self):
        def op():
            q=self.parse_numbers(self.minp);typ=self.mc.get()
            if typ.startswith("Kinematics"):u,a,tt=q;return f"v = {u+a*tt}\ns = {u*tt+0.5*a*tt**2}\nv² = {u*u+2*a*(u*tt+0.5*a*tt**2)}"
            if typ=="Projectile range":u,ang,g=q;return f"Range = {u*u*math.sin(2*math.radians(ang))/g}\nMax height = {u*u*math.sin(math.radians(ang))**2/(2*g)}"
            if typ.startswith("Newton"):m,a=q;return f"F = {m*a} N"
            if typ.startswith("Weight"):m,g=q;return f"W = {m*g} N"
            if typ.startswith("Density"):m,v=q;return f"Density = {m/v} kg/m³"
            if typ.startswith("Pressure"):force,area=q;return f"Pressure = {force/area} Pa"
            if typ.startswith("Work"):force,d,ang=q;return f"Work = {force*d*math.cos(math.radians(ang))} J"
            if typ.startswith("Kinetic"):m,v=q;return f"KE = {0.5*m*v*v} J"
            if typ.startswith("Potential"):m,g,h=q;return f"PE = {m*g*h} J"
            if typ.startswith("Spring"):k,dx=q;return f"Spring force = {-k*dx} N\nStored energy = {0.5*k*dx*dx} J"
            if typ.startswith("Stress"):force,area=q;return f"Stress = {force/area} Pa (strain needs original length and extension)"
            p,l=q;return f"Maximum bending moment = {p*l/4} N·m (central point load, simply supported beam)"
        self.run_guarded(self.mechout,op)

    # Signal processing
    def build_signals(self):
        f=self.tabs["Signals"];self.label(f,"Signal samples, comma-separated");self.sigdata=self.entry(f,"0,1,0,-1,0,1,0,-1")
        self.label(f,"Sampling rate in Hz");self.fs=self.entry(f,"1000")
        bar=tk.Frame(f,bg=APP_BG);bar.pack(fill="x",padx=8,pady=5)
        for n,fn in [("FFT magnitude",self.do_fft),("Convolution",self.do_convolution),("Correlation",self.do_correlation),("Low-pass filter",self.do_filter),("Signal statistics",self.signal_stats)]:self.button(bar,n,fn)
        self.sigout=self.output(f,10)
    def signal_array(self):return np.array(self.parse_numbers(self.sigdata),dtype=float)
    def do_fft(self):
        def op():
            a=self.signal_array(); fs=float(self.fs.get()); spec=np.abs(fft.rfft(a));freq=fft.rfftfreq(len(a),1/fs)
            return "Frequency (Hz) : magnitude\n"+"\n".join(f"{f:.6g} : {v:.6g}" for f,v in zip(freq,spec))
        self.run_guarded(self.sigout,op)
    def do_convolution(self):
        def op():return np.convolve(self.signal_array(),self.signal_array()).tolist()
        self.run_guarded(self.sigout,op)
    def do_correlation(self):
        def op():return np.correlate(self.signal_array(),self.signal_array(),mode="full").tolist()
        self.run_guarded(self.sigout,op)
    def do_filter(self):
        def op():
            a=self.signal_array();fs=float(self.fs.get());cut= min(fs*.2,fs/2-1e-9)
            if cut<=0:raise ValueError("Sampling rate must be positive")
            sos=signal.butter(4,cut,fs=fs,output="sos"); filtered=signal.sosfiltfilt(sos,a) if len(a)>15 else signal.sosfilt(sos,a)
            return "Low-pass filtered samples:\n"+str(filtered.tolist())+"\nNote: cutoff defaults to min(0.2·fs, Nyquist margin)."
        self.run_guarded(self.sigout,op)
    def signal_stats(self):
        def op():
            a=self.signal_array();return f"N={len(a)}\nMean={np.mean(a)}\nRMS={np.sqrt(np.mean(a*a))}\nPeak={np.max(np.abs(a))}\nVariance={np.var(a)}"
        self.run_guarded(self.sigout,op)

    # Number bases
    def build_bases(self):
        f=self.tabs["Number Systems"];self.label(f,"Integer (supports negative numbers)");self.bval=self.entry(f,"255")
        self.label(f,"Input base");self.base=ttk.Combobox(f,state="readonly",values=["2 - Binary","8 - Octal","10 - Decimal","16 - Hexadecimal"]);self.base.pack(fill="x",padx=12,pady=5);self.base.current(2)
        self.button(f,"Convert",self.convert_base);self.bout=self.output(f,8)
    def convert_base(self):
        def op():
            b=int(self.base.get().split()[0]);n=int(self.bval.get().strip(),b)
            return f"Binary      : {bin(n)}\nOctal       : {oct(n)}\nDecimal     : {n}\nHexadecimal : {hex(n)}\n\nUnsigned bit lengths: {abs(n).bit_length()}"
        self.run_guarded(self.bout,op)

    # History
    def build_history(self):
        f=self.tabs["History"];self.hbox=tk.Listbox(f,bg=PANEL,fg=FG,font=("Consolas",10),relief="flat");self.hbox.pack(fill="both",expand=True,padx=12,pady=12)
        bar=tk.Frame(f,bg=APP_BG);bar.pack(fill="x",padx=8)
        self.button(bar,"Copy selected to scientific input",self.use_history);self.button(bar,"Clear history",self.clear_history,BTN)
    def refresh_history(self):
        if hasattr(self,"hbox"):
            self.hbox.delete(0,"end")
            for item in reversed(self.history[-500:]):self.hbox.insert("end",item)
    def use_history(self):
        sel=self.hbox.curselection()
        if sel:
            self.notebook.select(self.tabs["Scientific"]);self.expr.delete(0,"end");self.expr.insert(0,self.hbox.get(sel[0]))
    def clear_history(self):self.history.clear();self.refresh_history()

if __name__ == "__main__":
    root=tk.Tk()
    app=EngineeringWorkbench(root)
    root.mainloop()
