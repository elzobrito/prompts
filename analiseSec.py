import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ttkthemes import ThemedTk  # Para tema escuro
import os
import ollama
import threading
import hashlib
import datetime
import json

# ============================================================
# CONFIGURAÇÃO DO SERVIDOR LOCAL (OLLAMA)
# ============================================================
# O Ollama geralmente usa o endereço padrão http://localhost:11434
# Não é necessário configurar explicitamente, pois a biblioteca ollama já assume isso

# ============================================================
# LISTA DE VULNERABILIDADES A SEREM TESTADAS
# ============================================================
VULNERABILITIES = [
    "Cross-Site Scripting (XSS)",
    "SQL Injection",
    "Falta de verificação de autorização",
    "Corrupção de memória",
    "Session Riding",
    "Dereferência de ponteiro NULL",
    "Ponteiro pendente",
    "Travessia de diretório",
    "Leitura fora dos limites",
    "Upload de arquivo não restrito",
    "Injeção de shell",
    "Overflow de buffer clássico",
    "Marshalling, Unmarshaling",
    "Divulgação de informação",
    "Vazamento de memória",
    "Injeção de código",
    "Injeção de comando",
    "Falsificação de solicitação do lado do servidor (SSRF)",
    "Validação inadequada de entrada",
    "Verificação incorreta de autorização",
    "Referência direta de objeto inseguro (IDOR)",
    "Problemas de autenticação",
    "Problemas de autorização",
    "Overflow ou estouro de inteiro",
    "Condição de corrida"
]

# ============================================================
# FUNÇÃO PARA ANÁLISE DO CÓDIGO COM LLM (USANDO OLLAMA)
# ============================================================
def analyze_with_llm(file_content, model):
    """
    Envia o conteúdo do arquivo para o LLM local (Ollama) e testa cada vulnerabilidade listada.
    Retorna um dicionário com os resultados para cada vulnerabilidade no formato:
    {
      "nome_da_vulnerabilidade": "Sim - Descrição..." ou "Não"
    }
    """
    # Dividir o arquivo em linhas numeradas, para facilitar referência
    lines = file_content.splitlines()
    numbered_code = "\n".join(f"{i+1}: {line}" for i, line in enumerate(lines))

    # Prompt solicitando JSON estrito e referência de linhas (se possível)
    prompt_base = f"""
Analise o seguinte código e retorne **exatamente** um objeto JSON, sem qualquer texto adicional fora do JSON.
Este JSON deve conter cada vulnerabilidade (lista abaixo) como chave.
Para cada chave, retorne um objeto com:
  - "presente": "Sim" ou "Não"
  - "descricao": breve explicação, incluindo, se possível, a linha do código onde ocorre a falha.

Exemplo de resposta JSON (seguindo estritamente este padrão):
{{
  "Cross-Site Scripting (XSS)": {{
    "presente": "Sim",
    "descricao": "Encontrado ponto de injeção de script na linha 42."
  }},
  "SQL Injection": {{
    "presente": "Não",
    "descricao": ""
  }}
}}

Código (com numeração de linha):
{numbered_code}

Vulnerabilidades a verificar (use EXATAMENTE como chaves no JSON):
{VULNERABILITIES}
"""

    try:
        # Usar o cliente Ollama para enviar a solicitação com streaming
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt_base}],
            stream=True
        )

        # Acumular a resposta completa
        response_text = ""
        for chunk in response:
            response_text += chunk["message"]["content"]

        # Tentar fazer parse do JSON
        try:
            json_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Se o LLM não retornou JSON válido
            return {
                vuln: "Erro ao analisar (resposta fora de formato JSON)"
                for vuln in VULNERABILITIES
            }

        # Montar dicionário final no formato esperado
        results = {}
        for vuln in VULNERABILITIES:
            if vuln in json_data:
                status = json_data[vuln].get("presente", "Não")
                desc = json_data[vuln].get("descricao", "").strip()
                if status.lower() == "sim":
                    # Combinar "Sim" + descrição
                    results[vuln] = f"Sim - {desc}" if desc else "Sim"
                else:
                    results[vuln] = "Não"
            else:
                # Se não veio no JSON, considerar "Não"
                results[vuln] = "Não"

        return results

    except Exception as e:
        # Em caso de qualquer outra falha
        return {vuln: f"Erro ao analisar: {e}" for vuln in VULNERABILITIES}

# ============================================================
# FUNÇÃO PARA GERAR RELATÓRIO HTML
# ============================================================
def generate_html_report(results_dict):
    """
    Gera um relatório em HTML com os resultados da análise para cada arquivo.
    Recebe 'results_dict', que deve ser:
        {
          "caminho_arquivo": {
             "Cross-Site Scripting (XSS)": "Sim - Descrição",
             "SQL Injection": "Não",
             ...
          },
          ...
        }
    Retorna o conteúdo HTML e o nome do arquivo com base em um hash MD5.
    """
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
        html_content += f"<h2>Arquivo: {file_path}</h2>"
        html_content += """
        <table>
            <tr>
                <th>Vulnerabilidade</th>
                <th>Resultado</th>
            </tr>
        """
        for vuln, result in file_results.items():
            result_class = "vuln-present" if result.startswith("Sim") else ""
            html_content += (
                f"<tr><td>{vuln}</td>"
                f"<td class='{result_class}'>{result}</td></tr>"
            )
        html_content += "</table>"

    html_content += """
</body>
</html>
"""

    # Gerar hash MD5 com base na data e hora atuais
    data_hora = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    hash_md5 = hashlib.md5(data_hora.encode()).hexdigest()
    nome_arquivo = f"relatorio_{hash_md5}.html"

    return html_content, nome_arquivo

# ============================================================
# FUNÇÃO PARA ANALISAR O PROJETO
# ============================================================
def analyze_project(project_path, progress_var, current_file_var, result_list, model):
    """
    Percorre os arquivos na pasta do projeto, analisa cada um com o LLM e exibe os resultados.
    Ao final, gera um relatório em HTML.
    """
    current_file_var.set("Iniciando análise com LLM...")
    progress_var.set(0)
    result_list.delete(0, tk.END)

    # Coletar todos os arquivos da pasta
    files = [os.path.join(root, file) for root, _, files in os.walk(project_path) for file in files]
    total_files = len(files)

    # Dicionário para armazenar resultados por arquivo
    all_results = {}

    for i, file_path in enumerate(files):
        current_file_var.set(f"Analisando {os.path.basename(file_path)}...")

        # Ler arquivo de forma segura, tratando binários
        file_content = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            # Se não for texto, podemos ignorar ou marcar como "Não analisável"
            result_list.insert(tk.END, f"{file_path}: Erro de decodificação (possível binário).")
            all_results[file_path] = {
                vuln: "Arquivo binário ou não-texto" for vuln in VULNERABILITIES
            }
            progress_var.set((i + 1) / total_files * 100)
            continue
        except Exception as e:
            error_msg = f"Erro ao ler o arquivo: {e}"
            result_list.insert(tk.END, f"{file_path}: {error_msg}")
            all_results[file_path] = {vuln: error_msg for vuln in VULNERABILITIES}
            progress_var.set((i + 1) / total_files * 100)
            continue

        # Analisar com LLM (via Ollama)
        results = analyze_with_llm(file_content, model)
        # Guardar no dicionário
        all_results[file_path] = results

        # Inserir no ListBox
        for vuln, result in results.items():
            result_list.insert(tk.END, f"{file_path}: {vuln} - {result}")

        progress_var.set((i + 1) / total_files * 100)
        # Força atualização da UI
        root.update_idletasks()

    # Gerar e salvar o relatório em HTML
    html_content, nome_arquivo = generate_html_report(all_results)
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write(html_content)

    messagebox.showinfo("Concluído", f"Análise concluída. Relatório salvo como {nome_arquivo}")

# ============================================================
# FUNÇÃO PARA INICIAR ANÁLISE (EM THREAD)
# ============================================================
def start_analysis():
    """
    Inicia a análise em uma thread separada para manter a interface responsiva.
    """
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
        args=(project_path, progress_var, current_file_var, result_list, model),
        daemon=True
    ).start()

# ============================================================
# FUNÇÃO PARA SELECIONAR A PASTA DO PROJETO
# ============================================================
def select_project_folder():
    """
    Abre um diálogo para selecionar a pasta do projeto.
    """
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        project_path_var.set(folder_selected)

# ============================================================
# CONSTRUÇÃO DA INTERFACE GRÁFICA (TKINTER)
# ============================================================
root = ThemedTk(theme="equilux")  # Tema escuro
root.title("Análise de Vulnerabilidades com LLM Local (Ollama)")
root.geometry("600x400")

project_path_var = tk.StringVar()
model_var = tk.StringVar()
current_file_var = tk.StringVar()
progress_var = tk.DoubleVar()

# Frame para seleção do modelo
model_frame = ttk.LabelFrame(root, text="Selecionar Modelo LLM")
model_frame.pack(pady=10, padx=10, fill="x")

model_label = ttk.Label(model_frame, text="Modelo:")
model_label.pack(side="left", padx=5)

# Lista de modelos disponíveis no Ollama (ajuste conforme necessário)
model_combobox = ttk.Combobox(
    model_frame,
    textvariable=model_var,
    values=["phi4"]  # Substitua pelos modelos que você tem no Ollama
)
model_combobox.pack(side="left", fill="x", expand=True, padx=5)

# Botão para selecionar a pasta do projeto
select_button = ttk.Button(root, text="Selecionar Pasta", command=select_project_folder)
select_button.pack(pady=10)

# Label para exibir o caminho da pasta selecionada
path_label = ttk.Label(root, textvariable=project_path_var)
path_label.pack(pady=5)

# Label para exibir o status da análise
current_file_label = ttk.Label(root, textvariable=current_file_var)
current_file_label.pack(pady=5)

# Barra de progresso
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill="x", padx=10, pady=5)

# Botão para iniciar a análise
analyze_button = ttk.Button(root, text="Iniciar Análise", command=start_analysis)
analyze_button.pack(pady=10)

# Lista para exibir os resultados
result_list = tk.Listbox(root, width=80, height=10)
result_list.pack(pady=10)

# Inicia o loop principal da interface
root.mainloop()