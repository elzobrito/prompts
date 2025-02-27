import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from tkinter import filedialog
import ollama
import uuid  # Importação da biblioteca UUID

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

def listar_arquivos(pasta, listbox):
    """Lista todos os arquivos de uma pasta na interface gráfica."""
    try:
        listbox.delete(0, tk.END)
        arquivos = os.listdir(pasta)
        for arquivo in arquivos:
            caminho_completo = os.path.join(pasta, arquivo)
            if os.path.isfile(caminho_completo):
                listbox.insert(tk.END, arquivo)
    except FileNotFoundError:
        listbox.insert(tk.END, f"A pasta '{pasta}' não foi encontrada.")
    except PermissionError:
        listbox.insert(tk.END, f"Permissão negada para acessar a pasta '{pasta}'.")

def select_project_folder(path_var, listbox):
    """Abre um diálogo para selecionar a pasta do projeto."""
    pasta = filedialog.askdirectory()
    if pasta:
        path_var.set(pasta)
        listar_arquivos(pasta, listbox)

def mostrar_conteudo_arquivo(listbox, pasta, text_widget):
    """Exibe o conteúdo do arquivo selecionado na área de texto."""
    try:
        selecionado = listbox.curselection()
        if selecionado:
            arquivo = listbox.get(selecionado[0])
            caminho_completo = os.path.join(pasta.get(), arquivo)
            with open(caminho_completo, "r", encoding="utf-8") as f:
                conteudo = f.read()
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, conteudo)
    except Exception as e:
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, f"Erro ao abrir arquivo: {str(e)}")

def analyze_with_llm(file_content, model):
    """Analisa o código com LLM e retorna as vulnerabilidades identificadas."""
    prompt = f"""
Analise o código a seguir e identifique possíveis vulnerabilidades com base na lista fornecida.

Código:
{file_content}

Vulnerabilidades a verificar:
{', '.join(VULNERABILITIES)}

Para cada vulnerabilidade detectada, forneça uma explicação detalhada, incluindo o motivo pelo qual o trecho de código é vulnerável e sugestões para corrigir o problema.
    """
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
        return response_text
    except Exception as e:
        return f"Erro ao analisar: {str(e)}"

def executar_analise(listbox, pasta, text_widget, model_var, progress_bar):
    """Executa a análise de segurança no arquivo selecionado e salva o resultado em um arquivo HTML."""
    def run_analysis():
        try:
            selecionado = listbox.curselection()
            if selecionado:
                arquivo = listbox.get(selecionado[0])
                caminho_completo = os.path.join(pasta.get(), arquivo)
                with open(caminho_completo, "r", encoding="utf-8") as f:
                    conteudo = f.read()
                progress_bar.start(10)
                resultado = analyze_with_llm(conteudo, model_var.get())
                progress_bar.stop()
                text_widget.delete("1.0", tk.END)
                text_widget.insert(tk.END, resultado)
                
                # Gerar um nome de arquivo único com UUID
                nome_arquivo = str(uuid.uuid4()) + ".html"
                caminho_html = os.path.join(pasta.get(), nome_arquivo)
                
                # Salvar o resultado em um arquivo HTML
                with open(caminho_html, "w", encoding="utf-8") as html_file:
                    html_file.write(f"<html><body><pre>{resultado}</pre></body></html>")
                
                # Informar ao usuário que o arquivo foi salvo
                messagebox.showinfo("Sucesso", f"Análise salva em {nome_arquivo}")
        except Exception as e:
            progress_bar.stop()
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, f"Erro ao analisar ou salvar arquivo: {str(e)}")
    
    threading.Thread(target=run_analysis, daemon=True).start()

# Interface gráfica
root = ThemedTk(theme="equilux")
root.title("Análise de Vulnerabilidades com LLM Local (Ollama)")
root.geometry("700x500")

frame_top = ttk.Frame(root)
frame_top.pack(fill="x", padx=10, pady=5)

model_label = ttk.Label(frame_top, text="Modelo:")
model_label.pack(side="left", padx=5)

model_var = tk.StringVar(value="phi4")
model_combobox = ttk.Combobox(frame_top, textvariable=model_var, values=["phi4"])
model_combobox.pack(side="left", fill="x", expand=True, padx=5)

project_path_var = tk.StringVar()
select_button = ttk.Button(frame_top, text="Selecionar Pasta", command=lambda: select_project_folder(project_path_var, result_list))
select_button.pack(side="left", padx=5)

frame_middle = ttk.Frame(root)
frame_middle.pack(fill="both", expand=True, padx=10, pady=5)

result_list = tk.Listbox(frame_middle, width=50, height=15)
result_list.pack(side="left", fill="both", expand=True, padx=5)

analyze_button = ttk.Button(frame_middle, text="Analisar", command=lambda: mostrar_conteudo_arquivo(result_list, project_path_var, content_text))
analyze_button.pack(side="left", padx=5, pady=5, fill="y")

frame_bottom = ttk.Frame(root)
frame_bottom.pack(fill="x", padx=10, pady=5)

content_label = ttk.Label(frame_bottom, text="Conteúdo")
content_label.pack(anchor="w")

content_text = tk.Text(frame_bottom, height=10)
content_text.pack(fill="both", expand=True, padx=5, pady=5)

progress_bar = ttk.Progressbar(frame_bottom, mode='indeterminate')
progress_bar.pack(fill="x", padx=10, pady=5)

execute_button = ttk.Button(frame_bottom, text="Executar", command=lambda: executar_analise(result_list, project_path_var, content_text, model_var, progress_bar))
execute_button.pack(side="right", padx=5, pady=5)

root.mainloop()