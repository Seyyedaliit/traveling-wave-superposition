# Traveling Wave Superposition Simulator

An interactive Python desktop application for visualizing two traveling waves and their real-time superposition (interference), built with **Tkinter**, **NumPy**, and **Matplotlib**.

## Physics Model

Each wave is modeled as:

$$y(x, t) = E_0 \sin(k x + s \omega t + \phi)$$

where $s = -1$ represents propagation in the $+x$ direction (right-traveling: $kx - \omega t$) and $s = +1$ represents propagation in the $-x$ direction (left-traveling: $kx + \omega t$). The resulting superposition is computed as $y_{\text{total}} = y_1 + y_2$.

## Features

- **Real-Time Wave Animation:** Smoothly plots Wave 1, Wave 2, and their combined interference result simultaneously.
- **Interactive Parameter Controls:** Modify amplitude ($E_0$), frequency ($f$), wave number ($k$), angular frequency ($\omega$), initial phase ($\phi$), and propagation direction (`+x` or `-x`) for each wave independently.
- **Automatic Wave Number Calculation:** Updating frequency $f$ automatically updates $k = \frac{2\pi f}{c}$ based on the configured wave speed $c$.
- **Medium & Domain Controls:** Configure wave speed $c$, spatial domain length $x_{\max}$, and grid resolution $N$.
- **Physics Presets:**
  - **User Default**
  - **Standing Wave** (two identical waves traveling in opposite directions)
  - **Wave Beats** (two co-propagating waves with slightly different frequencies)
  - **Destructive Interference** (equal waves with a $\pi$ phase difference)
- **Playback & Display Controls:** Play/Pause, Reset ($t = 0$), speed scaling (`0.1x` to `5.0x`), layer visibility toggles, grid toggle, Matplotlib navigation toolbar, and live phase velocity readouts ($v = \omega / k$) in the status bar.

## Keyboard Shortcuts

- `Space` — Play / Pause animation
- `R` — Reset time to $t = 0$
- `Enter` — Apply edited parameter values

## Installation & Usage

### Prerequisites

- Python 3.8+ (with `tkinter` support, included in standard Python installations on Windows/macOS)
- `numpy`
- `matplotlib`

### Run Locally

```bash
git clone https://github.com/Seyyedaliit/traveling-wave-superposition.git
cd traveling-wave-superposition
pip install -r requirements.txt
python wave_superposition.py
```

## Project Structure

```text
traveling-wave-superposition/
├── wave_superposition.py   # Main Tkinter + Matplotlib application
├── requirements.txt        # Python dependencies
├── .gitignore
└── README.md
```
