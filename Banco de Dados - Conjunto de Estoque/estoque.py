import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# ==========================================
# 1. DATABASE HELPER
# ==========================================
class DatabaseHelper:
    FILE_NAME = "estoque.json"

    @staticmethod
    def initialize_database():
        if not os.path.exists(DatabaseHelper.FILE_NAME):
            DatabaseHelper.salvar_dados([])

    @staticmethod
    def carregar_dados():
        if not os.path.exists(DatabaseHelper.FILE_NAME):
            return []
        try:
            with open(DatabaseHelper.FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    @staticmethod
    def salvar_dados(lojas):
        with open(DatabaseHelper.FILE_NAME, 'w', encoding='utf-8') as f:
            # ensure_ascii=False permite salvar acentuação normalmente, equivalente ao UnicodeRanges do C#
            json.dump(lojas, f, indent=2, ensure_ascii=False)

# ==========================================
# 2. STORE FORM (COM BUSCA E CARDS)
# ==========================================
class StoreWindow(tk.Toplevel):
    def __init__(self, parent, loja_nome):
        super().__init__(parent)
        self.loja_nome = loja_nome
        self.nome_produto_original = ""
        
        self.title(f"Estoque: {self.loja_nome}")
        self.geometry("800x700")
        self.configure(bg="#2C3E50")
        self.grab_set() # Foca nesta janela

        self.configurar_interface()
        self.carregar_produtos()

    def configurar_interface(self):
        # --- Painel do Topo (Formulário) ---
        painel_topo = tk.Frame(self, bg="#34495E", height=140)
        painel_topo.pack(side=tk.TOP, fill=tk.X)

        # Campos
        self.txt_nome = self.criar_campo(painel_topo, "Produto:", 20, 20)
        self.txt_quantidade = self.criar_campo(painel_topo, "Quantidade:", 200, 20)
        self.txt_fornecedor = self.criar_campo(painel_topo, "Fornecedor:", 380, 20)
        self.txt_preco = self.criar_campo(painel_topo, "Preço (R$):", 560, 20)

        # Botões
        self.criar_botao(painel_topo, "Adicionar", "#27AE60", 20, 80, self.adicionar_produto)
        self.criar_botao(painel_topo, "Atualizar", "#2980B9", 110, 80, self.atualizar_produto)
        self.criar_botao(painel_topo, "Deletar", "#C0392B", 200, 80, self.deletar_produto)
        
        # Botão limpar seleção
        tk.Button(painel_topo, text="Limpar Campos", bg="#7F8C8D", fg="white", 
                  command=self.limpar_campos, font=("Segoe UI", 9, "bold"), relief=tk.FLAT).place(x=290, y=80, width=120, height=35)

        # --- Painel de Busca ---
        painel_busca = tk.Frame(self, bg="#2C3E50", pady=10)
        painel_busca.pack(side=tk.TOP, fill=tk.X, padx=20)
        
        tk.Label(painel_busca, text="Buscar Produto:", bg="#2C3E50", fg="white", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.txt_busca = tk.Entry(painel_busca, width=40, font=("Segoe UI", 10))
        self.txt_busca.pack(side=tk.LEFT, padx=10)
        self.txt_busca.bind("<KeyRelease>", self.filtrar_produtos) # Atualiza a busca em tempo real

        # --- Área de Cards (Scrollable) ---
        self.canvas = tk.Canvas(self, bg="#2C3E50", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#2C3E50")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

    def criar_campo(self, parent, texto, x, y):
        tk.Label(parent, text=texto, bg="#34495E", fg="white", font=("Segoe UI", 9, "bold")).place(x=x, y=y)
        entry = tk.Entry(parent, width=22)
        entry.place(x=x, y=y+20)
        return entry

    def criar_botao(self, parent, texto, cor, x, y, comando):
        btn = tk.Button(parent, text=texto, bg=cor, fg="white", font=("Segoe UI", 9, "bold"), 
                        relief=tk.FLAT, cursor="hand2", command=comando)
        btn.place(x=x, y=y, width=80, height=35)
        return btn

    def renderizar_cards(self, produtos):
        # Limpa os cards antigos
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for prod in produtos:
            # Container do Card
            card = tk.Frame(self.scrollable_frame, bg="white", bd=2, relief=tk.GROOVE, padx=10, pady=10)
            card.pack(fill=tk.X, pady=5, padx=5, expand=True)
            
            # Informações do Card
            tk.Label(card, text=prod["Nome"], font=("Segoe UI", 12, "bold"), bg="white").pack(anchor=tk.W)
            
            info_frame = tk.Frame(card, bg="white")
            info_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(info_frame, text=f"Qtd: {prod['Quantidade']}", bg="white", fg="#7F8C8D", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 20))
            tk.Label(info_frame, text=f"Fornecedor: {prod['Fornecedor']}", bg="white", fg="#7F8C8D", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 20))
            tk.Label(info_frame, text=f"Preço: R$ {prod['Preco']:.2f}".replace('.', ','), bg="white", fg="#27AE60", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

            # Evento de clique no card (e seus filhos) para selecionar
            for widget in (card, info_frame) + tuple(card.winfo_children()) + tuple(info_frame.winfo_children()):
                widget.bind("<Button-1>", lambda e, p=prod: self.selecionar_produto(p))

    def carregar_produtos(self):
        lojas = DatabaseHelper.carregar_dados()
        loja = next((l for l in lojas if l["Nome"] == self.loja_nome), None)
        
        if loja:
            self.produtos_atuais = loja.get("Produtos", [])
            self.renderizar_cards(self.produtos_atuais)
        
        self.limpar_campos()

    def filtrar_produtos(self, event=None):
        termo = self.txt_busca.get().lower()
        produtos_filtrados = [p for p in self.produtos_atuais if termo in p["Nome"].lower()]
        self.renderizar_cards(produtos_filtrados)

    def selecionar_produto(self, produto):
        self.nome_produto_original = produto["Nome"]
        self.txt_nome.delete(0, tk.END); self.txt_nome.insert(0, produto["Nome"])
        self.txt_quantidade.delete(0, tk.END); self.txt_quantidade.insert(0, produto["Quantidade"])
        self.txt_fornecedor.delete(0, tk.END); self.txt_fornecedor.insert(0, produto["Fornecedor"])
        self.txt_preco.delete(0, tk.END); self.txt_preco.insert(0, str(produto["Preco"]))

    def limpar_campos(self):
        self.nome_produto_original = ""
        self.txt_nome.delete(0, tk.END)
        self.txt_quantidade.delete(0, tk.END)
        self.txt_fornecedor.delete(0, tk.END)
        self.txt_preco.delete(0, tk.END)

    def validar_campos(self):
        try:
            qtd = int(self.txt_quantidade.get())
            preco = float(self.txt_preco.get().replace(',', '.'))
            nome = self.txt_nome.get().strip()
            if not nome:
                raise ValueError()
            return nome, qtd, preco
        except ValueError:
            messagebox.showwarning("Aviso", "Verifique os campos. Quantidade deve ser inteira e preço numérico.")
            return None, None, None

    def adicionar_produto(self):
        nome, qtd, preco = self.validar_campos()
        if not nome: return

        lojas = DatabaseHelper.carregar_dados()
        loja = next((l for l in lojas if l["Nome"] == self.loja_nome), None)
        
        if loja is not None:
            # Evita nomes duplicados
            if any(p["Nome"] == nome for p in loja["Produtos"]):
                messagebox.showerror("Erro", "Produto já existe.")
                return

            loja["Produtos"].append({
                "Nome": nome, "Quantidade": qtd, "Fornecedor": self.txt_fornecedor.get(), "Preco": preco
            })
            DatabaseHelper.salvar_dados(lojas)
            self.carregar_produtos()
            self.txt_busca.delete(0, tk.END) # Reseta a busca

    def atualizar_produto(self):
        if not self.nome_produto_original: return
        nome, qtd, preco = self.validar_campos()
        if not nome: return

        lojas = DatabaseHelper.carregar_dados()
        loja = next((l for l in lojas if l["Nome"] == self.loja_nome), None)
        
        if loja is not None:
            prod = next((p for p in loja["Produtos"] if p["Nome"] == self.nome_produto_original), None)
            if prod:
                prod["Nome"] = nome
                prod["Quantidade"] = qtd
                prod["Fornecedor"] = self.txt_fornecedor.get()
                prod["Preco"] = preco
                DatabaseHelper.salvar_dados(lojas)
                self.carregar_produtos()
                self.txt_busca.delete(0, tk.END)

    def deletar_produto(self):
        if not self.nome_produto_original: return
        lojas = DatabaseHelper.carregar_dados()
        loja = next((l for l in lojas if l["Nome"] == self.loja_nome), None)
        
        if loja is not None:
            loja["Produtos"] = [p for p in loja["Produtos"] if p["Nome"] != self.nome_produto_original]
            DatabaseHelper.salvar_dados(lojas)
            self.carregar_produtos()
            self.txt_busca.delete(0, tk.END)


# ==========================================
# 3. MAIN FORM (LISTA DE LOJAS)
# ==========================================
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.nome_loja_original = ""

        self.title("Gerenciador de Comércio - Lojas (JSON)")
        self.geometry("600x500")
        self.configure(bg="#2C3E50")
        
        self.configurar_interface()
        self.carregar_lojas()

    def configurar_interface(self):
        painel_topo = tk.Frame(self, bg="#34495E", height=100)
        painel_topo.pack(side=tk.TOP, fill=tk.X)

        tk.Label(painel_topo, text="Nome da Loja:", bg="#34495E", fg="white", font=("Segoe UI", 10, "bold")).place(x=20, y=20)
        self.txt_nome_loja = tk.Entry(painel_topo, font=("Segoe UI", 10))
        self.txt_nome_loja.place(x=20, y=45, width=250)

        self.criar_botao(painel_topo, "Adicionar", "#27AE60", 290, 40, self.adicionar_loja)
        self.criar_botao(painel_topo, "Atualizar", "#2980B9", 380, 40, self.atualizar_loja)
        self.criar_botao(painel_topo, "Deletar", "#C0392B", 470, 40, self.deletar_loja)

        # Usando Treeview como a tabela de Lojas
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#ECF0F1", foreground="black", rowheight=30, fieldbackground="#ECF0F1")
        style.map('Treeview', background=[('selected', 'limegreen')])

        self.tree = ttk.Treeview(self, columns=("Nome",), show="headings")
        self.tree.heading("Nome", text="NOME DA LOJA (Duplo clique para abrir)")
        self.tree.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.tree.bind("<ButtonRelease-1>", self.selecionar_loja)
        self.tree.bind("<Double-1>", self.abrir_loja)

    def criar_botao(self, parent, texto, cor, x, y, comando):
        btn = tk.Button(parent, text=texto, bg=cor, fg="white", font=("Segoe UI", 9, "bold"), 
                        relief=tk.FLAT, cursor="hand2", command=comando)
        btn.place(x=x, y=y, width=80, height=35)
        return btn

    def carregar_lojas(self):
        lojas = DatabaseHelper.carregar_dados()
        self.tree.delete(*self.tree.get_children())
        for loja in lojas:
            self.tree.insert("", tk.END, values=(loja["Nome"],))
        
        self.nome_loja_original = ""
        self.txt_nome_loja.delete(0, tk.END)

    def selecionar_loja(self, event):
        item_selecionado = self.tree.selection()
        if item_selecionado:
            self.nome_loja_original = self.tree.item(item_selecionado[0], "values")[0]
            self.txt_nome_loja.delete(0, tk.END)
            self.txt_nome_loja.insert(0, self.nome_loja_original)

    def abrir_loja(self, event):
        item_selecionado = self.tree.selection()
        if item_selecionado:
            nome_loja = self.tree.item(item_selecionado[0], "values")[0]
            StoreWindow(self, nome_loja)

    def adicionar_loja(self):
        nome = self.txt_nome_loja.get().strip()
        if not nome: return
        
        lojas = DatabaseHelper.carregar_dados()
        if any(l["Nome"] == nome for l in lojas):
            messagebox.showwarning("Aviso", "Loja já existe!")
            return

        lojas.append({"Nome": nome, "Produtos": []})
        DatabaseHelper.salvar_dados(lojas)
        self.carregar_lojas()

    def atualizar_loja(self):
        novo_nome = self.txt_nome_loja.get().strip()
        if not self.nome_loja_original or not novo_nome: return

        lojas = DatabaseHelper.carregar_dados()
        loja = next((l for l in lojas if l["Nome"] == self.nome_loja_original), None)
        if loja:
            loja["Nome"] = novo_nome
            DatabaseHelper.salvar_dados(lojas)
            self.carregar_lojas()

    def deletar_loja(self):
        if not self.nome_loja_original: return
        if messagebox.askyesno("Confirmar", "Excluir loja e todo seu estoque?"):
            lojas = DatabaseHelper.carregar_dados()
            lojas = [l for l in lojas if l["Nome"] != self.nome_loja_original]
            DatabaseHelper.salvar_dados(lojas)
            self.carregar_lojas()


# ==========================================
# 4. ENTRY POINT
# ==========================================
if __name__ == "__main__":
    DatabaseHelper.initialize_database()
    app = MainWindow()
    app.mainloop()