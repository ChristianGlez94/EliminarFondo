from flask import Flask, render_template, request, send_file, jsonify, url_for
from rembg import remove
from PIL import Image
import os
import tempfile
import io
import socket
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import webbrowser
import time

app = Flask(__name__)

# Encuentra un puerto libre
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # Usa el puerto 0 para que el sistema asigne uno libre
        return s.getsockname()[1]

# Ventana de Confirmación
def show_confirmation_window():
    window = tk.Tk()
    window.title("Instalación de la Aplicación")
    window.geometry("400x200")
    window.resizable(False, False)

    label = tk.Label(window, text="¿Deseas iniciar la aplicación?", font=("Arial", 12))
    label.pack(pady=20)

    def accept():
        window.destroy()
        Thread(target=show_loading_window).start()  # Mostrar la barra de progreso
        start_flask_app()  # Iniciar Flask

    def cancel():
        window.destroy()
        messagebox.showinfo("Instalación Cancelada", "La instalación ha sido cancelada.")

    btn_accept = tk.Button(window, text="Aceptar", command=accept, width=10, bg="green", fg="white")
    btn_accept.pack(side=tk.LEFT, padx=50, pady=20)

    btn_cancel = tk.Button(window, text="Cancelar", command=cancel, width=10, bg="red", fg="white")
    btn_cancel.pack(side=tk.RIGHT, padx=50, pady=20)

    window.mainloop()

# Ventana de Progreso
def show_loading_window():
    window = tk.Tk()
    window.title("Cargando la Aplicación")
    window.geometry("400x200")
    window.resizable(False, False)

    label = tk.Label(window, text="Cargando, por favor espera...", font=("Arial", 12))
    label.pack(pady=20)

    # Barra de progreso
    progress = ttk.Progressbar(window, orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress.pack(pady=10)

    progress_label = tk.Label(window, text="0%", font=("Arial", 10))
    progress_label.pack()

    # Animar la barra de progreso
    for i in range(101):  # Del 0 al 100
        time.sleep(0.05)  # Ajusta la velocidad de la animación
        progress['value'] = i
        progress_label.config(text=f"{i}%")
        window.update_idletasks()  # Actualiza la ventana

    window.destroy()

# Abrir navegador automáticamente
def open_browser(port):
    time.sleep(1)  # Asegura que Flask esté listo antes de abrir el navegador
    webbrowser.open(f"http://localhost:{port}")

# Iniciar Flask
def start_flask_app():
    port = find_free_port()
    Thread(target=open_browser, args=(port,)).start()
    app.run(host="0.0.0.0", port=port)

@app.route('/')
def index():
    """Renderiza la página principal con imágenes por defecto."""
    return render_template(
        'index.html',
        default_original=url_for('static', filename='before.png'),
        default_processed=url_for('static', filename='after.png')
    )

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/privacidad')
def privacidad():
    return render_template('privacidad.html')

@app.route('/aviso_legal')
def aviso_legal():
    return render_template('aviso_legal.html')

@app.route('/process_image', methods=['POST'])
def process_image_route():
    """Procesa la imagen principal para eliminar el fondo."""
    if 'image' not in request.files:
        return jsonify({'error': 'No se ha subido la imagen principal.'}), 400

    try:
        file = request.files['image']
        input_image = Image.open(io.BytesIO(file.read()))
        input_image = input_image.convert("RGBA")

        # Eliminar fondo
        input_bytes = io.BytesIO()
        input_image.save(input_bytes, format="PNG")
        input_bytes = input_bytes.getvalue()
        output_bytes = remove(input_bytes)

        # Guardar la imagen en el sistema temporal
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, 'output_no_background.png')
        with open(temp_path, 'wb') as out_file:
            out_file.write(output_bytes)

        return jsonify({'message': 'Imagen procesada con éxito.', 'filename': temp_path}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_background', methods=['POST'])
def add_background_route():
    """Agrega un fondo nuevo a la imagen."""
    if 'image' not in request.files or 'background' not in request.files:
        return jsonify({'error': 'Faltan archivos (imagen principal o fondo).'}), 400

    try:
        file = request.files['image']
        input_image = Image.open(io.BytesIO(file.read()))
        input_image = input_image.convert("RGBA")

        # Eliminar fondo si es necesario
        input_bytes = io.BytesIO()
        input_image.save(input_bytes, format="PNG")
        input_bytes = input_bytes.getvalue()

        try:
            output_bytes = remove(input_bytes)
        except Exception:
            output_bytes = input_bytes  # Si ya está procesada

        processed_image = Image.open(io.BytesIO(output_bytes))

        # Leer el fondo
        bg_file = request.files['background']
        background_image = Image.open(io.BytesIO(bg_file.read()))
        background_image = background_image.convert("RGBA")
        background_image = background_image.resize(processed_image.size)

        # Combinar ambas imágenes
        combined_image = Image.alpha_composite(background_image, processed_image)

        # Guardar la imagen en el sistema temporal
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, 'output_with_background.png')
        combined_image.save(temp_path, format="PNG")

        return jsonify({'message': 'Fondo agregado con éxito.', 'filename': temp_path}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    """Permite descargar las imágenes procesadas."""
    try:
        return send_file(filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'Archivo no encontrado.'}), 404

if __name__ == "__main__":
    show_confirmation_window()
