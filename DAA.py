# visualizer_pro.py
# Algorithm Visualizer Pro - Tkinter + Matplotlib
import tkinter as tk
from tkinter import ttk, messagebox
import random, time, threading
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ========== Sorting implementations with yield for visualization ==========
def bubble_sort_gen(arr):
    a = arr.copy()
    n = len(a)
    for i in range(n):
        for j in range(0, n - i - 1):
            if a[j] > a[j+1]:
                a[j], a[j+1] = a[j+1], a[j]
                yield a, (j, j+1)
    yield a, None

def merge_sort_gen_helper(a, l, r, states):
    if r - l <= 1:
        return
    m = (l + r) // 2
    merge_sort_gen_helper(a, l, m, states)
    merge_sort_gen_helper(a, m, r, states)
    left = a[l:m]; right = a[m:r]
    i = j = 0; k = l
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            a[k] = left[i]; i += 1
        else:
            a[k] = right[j]; j += 1
        states.append((a.copy(), (k,)))
        k += 1
    while i < len(left):
        a[k] = left[i]; i += 1; k += 1
        states.append((a.copy(), (k-1,)))
    while j < len(right):
        a[k] = right[j]; j += 1; k += 1
        states.append((a.copy(), (k-1,)))

def merge_sort_gen(arr):
    a = arr.copy()
    states = []
    merge_sort_gen_helper(a, 0, len(a), states)
    for s in states:
        yield s
    yield a, None

def quick_sort_gen(arr):
    a = arr.copy()
    states = []
    def qs(l, r):
        if l >= r:
            return
        pivot = a[(l+r)//2]
        i, j = l, r
        while i <= j:
            while a[i] < pivot: i += 1
            while a[j] > pivot: j -= 1
            if i <= j:
                a[i], a[j] = a[j], a[i]
                states.append((a.copy(), (i, j)))
                i += 1; j -= 1
        qs(l, j); qs(i, r)
    qs(0, len(a)-1)
    for s in states:
        yield s
    yield a, None

# ========== Searching (no animation) ==========
def linear_search(arr, key):
    for i, v in enumerate(arr):
        if v == key:
            return i
    return -1

def binary_search(arr, key):
    lo, hi = 0, len(arr)-1
    while lo <= hi:
        mid = (lo+hi)//2
        if arr[mid] == key: return mid
        if arr[mid] < key: lo = mid+1
        else: hi = mid-1
    return -1

# ========== GUI ==========
class VisualizerApp:
    def __init__(self, root):
        self.root = root
        root.title("Algorithm Visualizer Pro")
        self.alg_var = tk.StringVar(value="Bubble Sort")
        self.size_var = tk.IntVar(value=50)
        self.speed_var = tk.DoubleVar(value=0.02)
        self.search_key_var = tk.IntVar(value=0)
        self.array = []
        self._build_ui()
        self.is_running = False

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)

        # controls
        ctrl = ttk.Frame(frm)
        ctrl.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(ctrl, text="Algorithm:").pack(side=tk.LEFT)
        ttk.Combobox(ctrl, textvariable=self.alg_var, values=[
            "Bubble Sort", "Merge Sort", "Quick Sort", "Linear Search", "Binary Search"
        ], width=18).pack(side=tk.LEFT, padx=4)
        ttk.Label(ctrl, text="Size:").pack(side=tk.LEFT, padx=(10,0))
        ttk.Spinbox(ctrl, from_=5, to=500, textvariable=self.size_var, width=6).pack(side=tk.LEFT)
        ttk.Label(ctrl, text="Speed (s):").pack(side=tk.LEFT, padx=(10,0))
        ttk.Spinbox(ctrl, from_=0.0, to=1.0, increment=0.01, textvariable=self.speed_var, width=6).pack(side=tk.LEFT)
        ttk.Button(ctrl, text="Generate Data", command=self.generate_data).pack(side=tk.LEFT, padx=6)
        ttk.Button(ctrl, text="Run", command=self.start).pack(side=tk.LEFT)
        ttk.Button(ctrl, text="Stop", command=self.stop).pack(side=tk.LEFT, padx=6)

        # canvas for matplotlib
        self.fig = Figure(figsize=(7,3))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=frm)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # status bar
        status = ttk.Frame(frm)
        status.pack(fill=tk.X)
        self.time_label = ttk.Label(status, text="Time: 0.000s")
        self.time_label.pack(side=tk.LEFT, padx=6)
        self.info_label = ttk.Label(status, text="")
        self.info_label.pack(side=tk.RIGHT, padx=6)

    def generate_data(self):
        n = self.size_var.get()
        self.array = [random.randint(1, n) for _ in range(n)]
        self.draw_bars(self.array, color='blue')
        self.info_label.config(text=f"Generated random array of size {n}")

    def draw_bars(self, arr, color='blue', highlight=None):
        self.ax.clear()
        x = list(range(len(arr)))
        self.ax.bar(x, arr, color=color)
        if highlight:
            for idx in (highlight if isinstance(highlight, (list,tuple)) else [highlight]):
                if idx is None: continue
                if 0 <= idx < len(arr):
                    self.ax.bar(idx, arr[idx], color='red')
        self.ax.set_title(self.alg_var.get())
        self.canvas.draw()

    def start(self):
        if self.is_running:
            return
        alg = self.alg_var.get()
        if not self.array:
            self.generate_data()
        self.is_running = True
        t = threading.Thread(target=self.run_algorithm, args=(alg,))
        t.daemon = True
        t.start()

    def stop(self):
        self.is_running = False

    def run_algorithm(self, alg):
        arr = self.array.copy()
        t0 = time.perf_counter()
        if alg == "Bubble Sort":
            gen = bubble_sort_gen(arr)
            for state, highlight in gen:
                if not self.is_running: break
                self.draw_bars(state, highlight=highlight)
                time.sleep(self.speed_var.get())
        elif alg == "Merge Sort":
            gen = merge_sort_gen(arr)
            for state, highlight in gen:
                if not self.is_running: break
                self.draw_bars(state, color='green', highlight=highlight)
                time.sleep(self.speed_var.get())
        elif alg == "Quick Sort":
            gen = quick_sort_gen(arr)
            for state, highlight in gen:
                if not self.is_running: break
                self.draw_bars(state, color='purple', highlight=highlight)
                time.sleep(self.speed_var.get())
        elif alg == "Linear Search":
            key = random.choice(arr)
            found = -1
            for i, v in enumerate(arr):
                if not self.is_running: break
                self.draw_bars(arr, highlight=i)
                time.sleep(self.speed_var.get())
                if v == key:
                    found = i
                    break
            messagebox.showinfo("Linear Search", f"Key {key} found at index {found}" if found!=-1 else "Not found")
        elif alg == "Binary Search":
            arr_sorted = sorted(arr)
            key = random.choice(arr_sorted)
            lo, hi = 0, len(arr_sorted)-1
            found = -1
            while lo <= hi and self.is_running:
                mid = (lo+hi)//2
                self.draw_bars(arr_sorted, highlight=mid)
                time.sleep(self.speed_var.get())
                if arr_sorted[mid] == key:
                    found = mid; break
                elif arr_sorted[mid] < key:
                    lo = mid+1
                else:
                    hi = mid-1
            messagebox.showinfo("Binary Search", f"Key {key} found at index {found}" if found!=-1 else "Not found")
        t1 = time.perf_counter()
        self.is_running = False
        self.time_label.config(text=f"Time: {t1-t0:.4f}s")
        self.info_label.config(text="Done.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VisualizerApp(root)
    root.mainloop()
