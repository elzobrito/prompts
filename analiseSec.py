import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ttkthemes import ThemedTk
import os
import ollama
import threading
import hashlib
import datetime
import json

# Lista de vulnerabilidades
VULNERABILITIES = [
    "Cross-Site Scripting (XSS)", "SQL Injection", "Falta de verificação de autorização",
    "Corrupção de memória", "Session Riding", "Dereferência de ponteiro NULL",
    "Ponteiro pendente", "Travessia de diretório", "Leitura fora dos limites",
    "Upload de arquivo não restrito", "Injeção de shell", "Overflow de buffer clássico",
    "Marshalling, Unmarshaling", "Divulgação de informação", "Vazamento de memória",
    "Injeção de código", "Injeção de comando", "Falsificação de solicitação do lado do servidor (SSRF)",
    "Validação inadequada de entrada", "Verificação incorreta de autorização",
    "Referência direta de objeto inseguro (IDOR)", "Problemas de autenticação",
    "Problemas de autorização", "Overflow ou estouro de inteiro", "Condição de corrida"
]

def analyze_with_llm(file_content, model):

    lines = file_content.splitlines()
    numbered_code = "\n".join(f"{i+1}: {line}" for i, line in enumerate(lines))

    prompt = f"""Analise o código a seguir e identifique possíveis vulnerabilidades com base na lista fornecida. Código: {numbered_code} Vulnerabilidades a verificar: {', '.join(VULNERABILITIES)} Para cada vulnerabilidade detectada, forneça uma explicação detalhada, incluindo o motivo pelo qual o trecho de código é vulnerável e sugestões para corrigir o problema."""

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        response_text = ""
        for chunk in response:
            if isinstance(chunk, dict) and "message" in chunk and "content" in chunk["message"]:
                response_text += chunk["message"]["content"]

        try:
            json_data = json.loads(response_text)
        except json.JSONDecodeError:
            return {vuln: "Erro ao analisar (resposta fora de formato JSON)" for vuln in VULNERABILITIES}

        results = {}
        for vuln in VULNERABILITIES:
            if vuln in json_data and isinstance(json_data[vuln], dict):
                status = json_data[vuln].get("presente", "Não")
                desc = json_data[vuln].get("descricao", "").strip()
                results[vuln] = f"Sim - {desc}" if status.lower() == "sim" and desc else status
            else:
                results[vuln] = "Não"
        return results

    except Exception as e:
        return {vuln: f"Erro ao analisar: {str(e)}" for vuln in VULNERABILITIES}

def generate_html_report(results_dict):
    """Gera um relatório em HTML com os resultados da análise."""
    html_content = """
<html>
<head>
    <title>Relatório de Vulnerabilidades</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }
        h1 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .vuln-present { color: red; }
    </style>
</head>
<body>
    <h1>Relatório de Vulnerabilidades</h1>
"""
    for file_path, file_results in results_dict.items():
        html_content += f"<h2>Arquivo: {file_path}</h2><table><tr><th>Vulnerabilidade</th><th>Resultado</th></tr>"
        for vuln, result in file_results.items():
            result_class = "vuln-present" if result.startswith("Sim") else ""
            html_content += f"<tr><td>{vuln}</td><td class='{result_class}'>{result}</td></tr>"
        html_content += "</table>"

    html_content += "</body></html>"
    data_hora = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    hash_md5 = hashlib.md5(data_hora.encode()).hexdigest()
    nome_arquivo = f"relatorio_{hash_md5}.html"
    return html_content, nome_arquivo

def analyze_project(project_path, progress_var, current_file_var, result_list, model, root):
    """Analisa todos os arquivos do projeto e gera um relatório."""
    current_file_var.set("Iniciando análise com LLM...")
    progress_var.set(0)
    result_list.delete(0, tk.END)

    files = [os.path.join(root, file) for root, _, files in os.walk(project_path) for file in files]
    total_files = len(files)
    all_results = {}

    for i, file_path in enumerate(files):
        current_file_var.set(f"Analisando {os.path.basename(file_path)}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            result_list.insert(tk.END, f"{file_path}: Arquivo binário ou não-texto")
            all_results[file_path] = {vuln: "Arquivo binário ou não-texto" for vuln in VULNERABILITIES}
            progress_var.set((i + 1) / total_files * 100)
            continue
        except Exception as e:
            error_msg = f"Erro ao ler o arquivo: {e}"
            result_list.insert(tk.END, f"{file_path}: {error_msg}")
            all_results[file_path] = {vuln: error_msg for vuln in VULNERABILITIES}
            progress_var.set((i + 1) / total_files * 100)
            continue

        results = analyze_with_llm(file_content, model)
        all_results[file_path] = results
        for vuln, result in results.items():
            result_list.insert(tk.END, f"{file_path}: {vuln} - {result}")
        progress_var.set((i + 1) / total_files * 100)
        root.update_idletasks()

    html_content, nome_arquivo = generate_html_report(all_results)
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write(html_content)
    messagebox.showinfo("Concluído", f"Análise concluída. Relatório salvo como {nome_arquivo}")

def start_analysis(project_path_var, model_var, progress_var, current_file_var, result_list, root):
    """Inicia a análise em uma thread separada."""
    project_path = project_path_var.get()
    model = model_var.get()
    if not project_path:
        messagebox.showwarning("Aviso", "Selecione uma pasta do projeto.")
        return
    if not model:
        messagebox.showwarning("Aviso", "Selecione um modelo LLM.")
        return

    threading.Thread(
        target=analyze_project,
        args=(project_path, progress_var, current_file_var, result_list, model, root),
        daemon=True
    ).start()

def select_project_folder(project_path_var):
    """Abre diálogo para selecionar a pasta do projeto."""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        project_path_var.set(folder_selected)

# Interface gráfica
root = ThemedTk(theme="equilux")
root.title("Análise de Vulnerabilidades com LLM Local (Ollama)")
root.geometry("600x400")

project_path_var = tk.StringVar()
model_var = tk.StringVar(value="phi4")  # Valor padrão
current_file_var = tk.StringVar()
progress_var = tk.DoubleVar()

model_frame = ttk.LabelFrame(root, text="Selecionar Modelo LLM")
model_frame.pack(pady=10, padx=10, fill="x")

model_label = ttk.Label(model_frame, text="Modelo:")
model_label.pack(side="left", padx=5)

model_combobox = ttk.Combobox(model_frame, textvariable=model_var, values=["phi4"])  # Ajuste conforme modelos disponíveis
model_combobox.pack(side="left", fill="x", expand=True, padx=5)

select_button = ttk.Button(root, text="Selecionar Pasta", command=lambda: select_project_folder(project_path_var))
select_button.pack(pady=10)

path_label = ttk.Label(root, textvariable=project_path_var)
path_label.pack(pady=5)

current_file_label = ttk.Label(root, textvariable=current_file_var)
current_file_label.pack(pady=5)

progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill="x", padx=10, pady=5)

analyze_button = ttk.Button(root, text="Iniciar Análise", command=lambda: start_analysis(project_path_var, model_var, progress_var, current_file_var, result_list, root))
analyze_button.pack(pady=10)

result_list = tk.Listbox(root, width=80, height=10)
result_list.pack(pady=10)

root.mainloop()