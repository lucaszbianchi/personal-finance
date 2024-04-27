from tkinter import *
from tkinter import Tk, ttk, messagebox, filedialog
from PIL import  Image, ImageTk
from tkinter.ttk import Progressbar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from tkcalendar import Calendar, DateEntry
from datetime import date, datetime

from view import inserir_categoria, inserir_receita, inserir_gastos, ver_categorias, ver_gastos, ver_receitas, tabela, deletar_gastos, deletar_receitas
from view import ver_credito, ver_vale, deletar_credito, deletar_valerefeição, deletar_categoria, atualizar_credito, atualizar_gastos, atualizar_receitas, atualizar_vale
from lerextratos import nubank_conta, nubank_credito, sodexo
def converter_data(data_str):
    # Converter string 'dd/mm/yyyy' para objeto datetime
    return datetime.strptime(data_str, '%d/%m/%Y')

################# cores ###############
co0 = "#2e2d2b"  # Preta
co1 = "#feffff"  # branca
co2 = "#4fa882"  # verde
co3 = "#38576b"  # valor
co4 = "#403d3d"   # letra
co5 = "#e06636"   # - profit
co6 = "#038cfc"   # azul
co7 = "#3fbfb9"   # verde
co8 = "#263238"   # + verde
co9 = "#e9edf5"   # + verde

colors = ['#5588bb', '#66bbbb','#99bb55', '#ee9944', '#444466', '#bb5555']

# Criar e configurar a janela
janela = Tk()
janela.title('Finance')
janela.geometry('1200x900')
janela.configure(background=co1)
janela.resizable(width=FALSE, height=FALSE)

style = ttk.Style(janela)
style.theme_use('clam')

# Definir os frames principais
frameCima = Frame(janela,width=1200, height=50, background= co1, relief='flat')
frameCima.grid(row=0,column=0,padx=3)

frameMeio = Frame(janela,width=1200, height=400, background= co1, pady=20,relief='raised')
frameMeio.grid(row=1,column=0, pady=1, padx=3, sticky=NSEW)

frameBaixo = Frame(janela,width=1200, height=489, background= co1, relief='flat')
frameBaixo.grid(row=2,column=0, pady=0, padx=3, sticky=NSEW)

# Criar um frame dividindo o frame do meio
frame_graficos = Frame(frameMeio, width=900, height=361, bg=co2)
frame_graficos.place(x=300, y=0)

# Criar 5 frames dividindo o frame de baixo
frame_tabela = Frame(frameBaixo, width=550, height=489,bg=co9)
frame_tabela.grid(row=0,column=0)

frame_despesas = Frame(frameBaixo, width=300, height=300,bg=co9)
frame_despesas.place(x=575, y=0)

frame_receitas = Frame(frameBaixo, width=300, height=180,bg=co9)
frame_receitas.place(x=885, y=0)

frame_config = Frame(frameBaixo, width=300, height=243,bg=co9)
frame_config.place(x=885, y=190)

frame_extrato = Frame(frameBaixo, width=300, height=123,bg=co9)
frame_extrato.place(x=575, y=310)


# Definir Título e Imagem do Head
app_img = Image.open('imagens/coin.png')
app_img = app_img.resize((45,45))
app_img = ImageTk.PhotoImage(app_img)

app_logo = Label(frameCima, image=app_img, text=' Personal Finance', width=1440, compound=LEFT, padx=5, relief=RAISED, anchor=NW, font=('Verdana 20 bold'), background= co1, fg=co4)
app_logo.place(x=0, y=0)

# Função a ser executada no botao_inserir_categoria
def nova_categoria():
    categoria = e_categoria.get()
    lista_inserir = [categoria]
    for i in lista_inserir:
        if i=='':
            messagebox.showerror('Erro', 'Preencha todos os campos')
            return

    inserir_categoria(lista_inserir)
    messagebox.showinfo('Sucesso', 'Os dados foram inseridos com sucesso')

    e_categoria.delete(0, 'end')

    dropdown_categoria['values'] = (ver_categorias())
# Função a ser executada no botao_inserir_receita
def nova_receita():
    fonte = 'Receita'
    descrição = e_descrição_receita.get()
    data = datetime.strptime(e_cal_receitas.get(), '%d/%m/%Y')
    valor = e_valor_receitas.get()
    
    lista_inserir = [fonte,descrição,data,valor]
    for i in lista_inserir:
        if i=='':
            messagebox.showerror('Erro', 'Preencha todos os campos')
            return
        
    inserir_receita(lista_inserir)
    messagebox.showinfo('Sucesso', 'Os dados foram inseridos com sucesso')

    e_cal_receitas.delete(0, 'end')
    e_valor_receitas.delete(0, 'end')

    atualizar_interface()
# Função a ser executada no botao_inserir_despesa
def nova_despesa():
    categoria = dropdown_categoria.get()
    descrição = e_descrição_despesa.get()
    data = datetime.strptime(e_cal_despesa.get(), '%d/%m/%Y')
    valor = int(e_valor_despesa.get())
    
    lista_inserir = [categoria, descrição, data, valor]
    for i in lista_inserir:
        if i=='':
            messagebox.showerror('Erro', 'Preencha todos os campos')
            return
    lista_inserir = [categoria, descrição, data, -valor]
        
    inserir_gastos(lista_inserir)
    messagebox.showinfo('Sucesso', 'Os dados foram inseridos com sucesso')

    dropdown_categoria.delete(0,'end')
    e_descrição_despesa.delete(0, 'end')
    e_cal_despesa.delete(0, 'end')
    e_valor_despesa.delete(0, 'end')

    atualizar_interface()
# Função a ser executada no botao_deletar
def deletar():
    try:
        treev_dados = tree.focus()
        treev_dicionario = tree.item(treev_dados)
        treev_lista = treev_dicionario['values']
        id = treev_lista[0]
        categoria = treev_lista[1]
        descrição =  treev_lista[2]

        if categoria == 'Receita': deletar_receitas([id])
        elif 'credito' in descrição: deletar_credito([id])
        elif 'sodexo' in descrição: deletar_valerefeição([id])
        else: deletar_gastos([id])

        messagebox.showinfo('Sucesso', 'Os dados foram deletados com sucesso')

        atualizar_interface()

    except IndexError:
        messagebox.showerror('Erro', 'Seleciona um dos dados na tabela')
def editar_registro_popup(id,categoria,descrição):
    def salvar():
        nova_categoria = combo_categoria.get()
        nova_descricao = entry_descricao.get()
        if categoria == 'Receita': atualizar_receitas(id, nova_categoria, nova_descricao)
        elif 'credito' in descrição:  atualizar_credito(id, nova_categoria, nova_descricao)
        elif 'sodexo' in descrição:  atualizar_vale(id, nova_categoria, nova_descricao)
        else: atualizar_gastos(id, nova_categoria, nova_descricao)
        messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")
        atualizar_interface()
        window.destroy()


    window = Toplevel()
    window.title("Editar Registro")

    label_categoria = ttk.Label(window, text="Nova Categoria:")
    label_categoria.grid(row=0, column=0, padx=5, pady=5)
    categorias = ver_categorias()  # Coloque suas categorias aqui
    combo_categoria = ttk.Combobox(window, values=categorias, state="readonly")
    combo_categoria.set(categoria)
    combo_categoria.grid(row=0, column=1, padx=5, pady=5)

    label_descricao = ttk.Label(window, text="Nova Descrição:")
    label_descricao.grid(row=1, column=0, padx=5, pady=5)
    entry_descricao = ttk.Entry(window)
    entry_descricao.insert(0, descrição)
    entry_descricao.grid(row=1, column=1, padx=5, pady=5)

    button_salvar = ttk.Button(window, text="Salvar", command=salvar)
    button_salvar.grid(row=2, columnspan=2, padx=5, pady=5)
def atualizar():
    try:
        treev_dados = tree.focus()
        treev_dicionario = tree.item(treev_dados)
        treev_lista = treev_dicionario['values']
        id = treev_lista[0]
        categoria = treev_lista[1]
        descrição =  treev_lista[2]
        editar_registro_popup(id=id,categoria=categoria,descrição=descrição)
    except IndexError:
        messagebox.showerror('Erro', 'Seleciona um dos dados na tabela')
# Função a ser executada no botao_pesquisar
def pesquisar_arquivo():
    # Abrir a caixa de diálogo para seleção de arquivo
    arquivo = filedialog.askopenfilename(title="Selecione um arquivo")
    if '/extratos' in arquivo: arquivo = arquivo.split('/extratos/')[1]
    else: messagebox.showerror('Erro', 'Escolha um arquivo da pasta extratos')
    # Verificar se um arquivo foi selecionado
    if arquivo:
        # Exibir o caminho do arquivo selecionado
        label_resultado.config(text=f"{arquivo}")
    else:
        # Se nenhum arquivo for selecionado
        label_resultado.config(text="Nenhum arquivo selecionado")
# Função a ser executada no botao_confirmar
def confirmar_extrato():
    arquivo = f'extratos/{label_resultado.cget("text")}'
    radio = selecionado.get()
    if radio == 'conta': nubank_conta(arquivo)
    elif radio == 'credito': nubank_credito(arquivo)
    elif radio == 'sodexo': sodexo(arquivo)
    selecionado.set(0)
    atualizar_interface()
# Função a ser executada no botao_reset
def reiniciar_dados():
    check = estado.get()
    if check == False: return
    for item in tree.get_children():
        treev_dicionario = tree.item(item)
        treev_lista = treev_dicionario['values']
        id = treev_lista[0]
        categoria = treev_lista[1]
        descrição =  treev_lista[2]

        if categoria == 'Receita': deletar_receitas([id])
        elif 'credito' in descrição: deletar_credito([id])
        elif 'sodexo' in descrição: deletar_valerefeição([id])
        else: deletar_gastos([id])

    messagebox.showinfo('Sucesso', 'Os planilha reiniciada com sucesso')
    estado.set(0)
    atualizar_interface()
# Função a ser executada no botao_confirmar_periodo
def confirmar_periodo():
    data_inicio = e_cal_periodo_inicio.get()
    data_fim = e_cal_periodo_fim.get()
    porcentagem(data_inicio=data_inicio, data_fim=data_fim)
    resumo(data_inicio=data_inicio, data_fim=data_fim)
    grafico_pie(data_inicio=data_inicio, data_fim=data_fim)
    mostrar_tabela(data_inicio=data_inicio, data_fim=data_fim)
# Funçao a ser executada no botao_confirmar_credito
# def confirmar_credito():
# Função a ser executada no botao_remover_categoria
def remover_categoria():
    categoria = e_categoria.get()
    lista_remover = [categoria]
    for i in lista_remover:
        if i=='':
            messagebox.showerror('Erro', 'Preencha todos os campos')
            return

    deletar_categoria(lista_remover)
    messagebox.showinfo('Sucesso', 'Os dados foram removidos com sucesso')

    e_categoria.delete(0, 'end')

    dropdown_categoria['values'] = (ver_categorias())
# Barra de progresso de porcentagem de receita gasta
def porcentagem(data_inicio=None, data_fim=None):
    l_nome = Label(frame_graficos, text="Porcentagem da Receita gasta", height=1, anchor=NW, font='VERDANA 12', bg=co1, fg=co4)
    l_nome.place(x=140,y=0)

    style = ttk.Style()
    style.theme_use('default')
    style.configure('black.Horizontal.TProgress', background='#daed6b')
    style.configure('TProgressbar',thickness=25)
    bar = Progressbar(frame_graficos, length=180, style='black.Horizontal.TProgressbar')
    bar.place(x=140, y=35)
    soma_receitas = sum([float(valor[4]) for valor in ver_receitas(data_inicio=data_inicio,data_fim=data_fim)])
    soma_despesas = sum([float(valor[4]) for valor in ver_gastos(data_inicio=data_inicio,data_fim=data_fim)])
    if soma_receitas != 0: valor = -soma_despesas*100/soma_receitas
    else: valor = 0
    bar['value'] = valor

    l_porcentagem = Label(frame_graficos, text=f"{valor:,.2f}%", anchor=NW, font='VERDANA 12', bg=co1, fg=co4)
    l_porcentagem.place(x=330, y=35)
# Grafico de barras com Renda, Despesas e Saldo
def grafico_bar():
    soma_receitas = sum([valor[3] for valor in ver_receitas()])
    soma_despesas = sum([valor[3] for valor in ver_gastos()])
    lista_categorias = ['Renda', 'Despesas', 'Saldo']
    lista_valores = [soma_receitas,soma_despesas,soma_receitas-soma_despesas]

    figura = plt.Figure(figsize=(4, 3.45), dpi=60)
    ax = figura.add_subplot(111)
    ax.autoscale(enable=True, axis='both', tight=None)

    ax.bar(lista_categorias, lista_valores,  color=colors, width=0.9)

    c = 0
    for i in ax.patches:
        # get_x pulls left or right; get_height pushes up or down
        ax.text(i.get_x()-.001, i.get_height()+.5,
                str("{:,.0f}".format(lista_valores[c])), fontsize=17, fontstyle='italic',  verticalalignment='bottom',color='dimgrey')
        c += 1

    ax.set_xticklabels(lista_categorias,fontsize=16)

    ax.patch.set_facecolor('#ffffff')
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.spines['bottom'].set_linewidth(1)
    ax.spines['right'].set_linewidth(0)
    ax.spines['top'].set_linewidth(0)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['left'].set_linewidth(1)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(bottom=False, left=False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(False, color='#EEEEEE')
    ax.xaxis.grid(False)

    canva = FigureCanvasTkAgg(figura, frameMeio)
    canva.get_tk_widget().place(x=10, y=70)
# Resumo em texto
def resumo(data_inicio=None, data_fim=None):

    soma_receitas = sum([float(valor[4]) for valor in ver_receitas(data_inicio=data_inicio,data_fim=data_fim)])
    soma_despesas = sum([float(valor[4]) for valor in ver_gastos(data_inicio=data_inicio,data_fim=data_fim)])
    if soma_receitas != 0: valor = -soma_despesas*100/soma_receitas

    l_linha = Label(frameMeio, text="", width=215, height=1,anchor=NW, font=('arial 1 '), bg='#545454',)
    l_linha.place(x=59, y=52)
    l_sumario = Label(frameMeio, text="Total Renda Mensal      ".upper(), height=1,anchor=NW, font=('Verdana 12'), bg=co1, fg='#83a9e6')
    l_sumario.place(x=56, y=35)
    l_sumario = Label(frameMeio, text='R$ {:,.2f}'.format(soma_receitas), height=1,anchor=NW, font=('arial 17 '), bg=co1, fg='#545454')
    l_sumario.place(x=56, y=70)

    l_linha = Label(frameMeio, text="", width=215, height=1,anchor=NW, font=('arial 1 '), bg='#545454',)
    l_linha.place(x=59, y=132)
    l_sumario = Label(frameMeio, text="Total Despesas Mensais".upper(), height=1,anchor=NW, font=('Verdana 12'), bg=co1, fg='#83a9e6')
    l_sumario.place(x=56, y=115)
    l_sumario = Label(frameMeio, text='R$ {:,.2f}'.format(soma_despesas), height=1,anchor=NW, font=('arial 17 '), bg=co1, fg='#545454')
    l_sumario.place(x=56, y=150)

    l_linha = Label(frameMeio, text="", width=215, height=1,anchor=NW, font=('arial 1 '), bg='#545454',)
    l_linha.place(x=59, y=207)
    l_sumario = Label(frameMeio, text="Total Saldo da Caixa    ".upper(), height=1,anchor=NW, font=('Verdana 12'), bg=co1, fg='#83a9e6')
    l_sumario.place(x=56, y=190)
    l_sumario = Label(frameMeio, text='R$ {:,.2f}'.format(soma_receitas+soma_despesas), height=1,anchor=NW, font=('arial 17 '), bg=co1, fg='#545454')
    l_sumario.place(x=56, y=220)
# Grafico de pizza com gastos de cada categoria
def grafico_pie(data_inicio=None, data_fim=None):
    figura = plt.Figure(figsize=(5,3), dpi=90)
    ax = figura.add_subplot(111)
    somas_categorias = {}

    # Calcular a soma dos gastos por categoria
    for gasto in ver_gastos(data_inicio=data_inicio,data_fim=data_fim):
        categoria = gasto[1]
        descrição = gasto[2]
        valor = -(gasto[4])
        if descrição == 'Pagamento de fatura': continue
        if categoria in somas_categorias:
            somas_categorias[categoria] += valor
        else:
            somas_categorias[categoria] = valor
    for credito in ver_credito(data_inicio=data_inicio,data_fim=data_fim):
        categoria = credito[1]
        valor = -(credito[4])
        if categoria in somas_categorias:
            somas_categorias[categoria] += valor
        else:
            somas_categorias[categoria] = valor
    # for vale in ver_vale(data_inicio=data_inicio,data_fim=data_fim):
    #     categoria = vale[1]
    #     valor = -(vale[4])
    #     if valor < 0: continue
    #     if categoria in somas_categorias:
    #         somas_categorias[categoria] += valor
    #     else:
    #         somas_categorias[categoria] = valor
    # Criar a lista de valores no estilo especificado
    lista_valores = [valor for (_, valor) in somas_categorias.items()]
    lista_categorias = [categoria for (categoria, _) in somas_categorias.items()]

    explode = []
    for i in lista_categorias:
        explode.append(0.05)
    ax.pie(lista_valores, explode=explode, wedgeprops=dict(width=0.2), autopct='%1.1f%%', colors=colors, shadow=True, startangle=90)
    ax.legend(lista_categorias, loc='center right', bbox_to_anchor=(1.55,0.50))

    canva_categoria = FigureCanvasTkAgg(figura, frame_graficos)
    canva_categoria.get_tk_widget().place(x=0, y=70)
# Tabela de Gastos e Receitas
def mostrar_tabela(data_inicio=None, data_fim=None):
    l_income = Label(frameMeio, text="Tabela Receitas e Despesas", height=1,anchor=NW, font=('Verdana 12'), bg=co1, fg=co4)
    l_income.place(x=5, y=350)

    tabela_head = ['#id', 'Categoria', 'Descrição', 'Data', 'valor']
    if data_inicio is None or data_fim is None: lista_itens = tabela()
    else: lista_itens = tabela(data_inicio=datetime.strptime(data_inicio, '%d/%m/%Y'),data_fim=datetime.strptime(data_fim, '%d/%m/%Y'))

    global tree

    tree = ttk.Treeview(frame_tabela, selectmode='extended', columns=tabela_head, show='headings', height=20)
    vsb = ttk.Scrollbar(frame_tabela, orient='vertical', command=tree.yview)
    hsb = ttk.Scrollbar(frame_tabela, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(column=0, row=0, sticky='nsew')
    vsb.grid(column=1, row=0, sticky='ns')
    hsb.grid(column=0, row=1, sticky='ew')

    hd=["center","center","center", "center", "center"]
    h=[30,100,300,67,50]
    n=0

    for col in tabela_head:
            tree.heading(col, text=col.title(), anchor=CENTER)
            # adjust the column's width to the header string
            tree.column(col, width=h[n],anchor=hd[n])

            n+=1

    for item in lista_itens:
        tree.insert('', 'end', values=item)

# Interface despesas ------------------------------------------------
l_head_despesa = Label(frame_despesas, text="INSIRA NOVAS DESPESAS", height=1,anchor=NW,relief="flat", font=('Verdana 10 bold'), bg=co1, fg=co4)
l_head_despesa.place(x=55, y=10)

l_categoria = Label(frame_despesas, text="Categoria", height=1,anchor=NW,relief="flat", font=('Ivy 10'), bg=co1, fg=co4)
l_categoria.place(x=55, y=50)

dropdown_categoria = ttk.Combobox(frame_despesas, width=10,font=('Ivy 10'))
dropdown_categoria['values'] = (ver_categorias())
dropdown_categoria.place(x=160, y=51)

l_descrição_despesa = Label(frame_despesas, text="Descrição", height=1,anchor=NW, font=('Ivy 10 '), bg=co1, fg=co4)
l_descrição_despesa.place(x=55, y=80)
e_descrição_despesa = Entry(frame_despesas, width=14, justify='left',relief="solid")
e_descrição_despesa.place(x=160, y=81)

l_cal_despesa = Label(frame_despesas, text="Data", height=1,anchor=NW, font=('Ivy 10 '), bg=co1, fg=co4)
l_cal_despesa.place(x=55, y=110)
e_cal_despesa = DateEntry(frame_despesas, locale='pt_BR', date_pattern='dd/MM/yyyy', width=12, background='darkblue', foreground='white', borderwidth=2)
e_cal_despesa.place(x=160, y=111)

l_valor_despesa = Label(frame_despesas, text="Valor (R$)", height=1,anchor=NW, font=('Ivy 10 '), bg=co1, fg=co4)
l_valor_despesa.place(x=55, y=140)
e_valor_despesa = Entry(frame_despesas, width=14, justify='left',relief="solid")
e_valor_despesa.place(x=160, y=141)

# Botao Inserir despesas
img_add_despesas  = Image.open('imagens/add.png')
img_add_despesas = img_add_despesas.resize((17,17))
img_add_despesas = ImageTk.PhotoImage(img_add_despesas)
botao_inserir_despesa = Button(frame_despesas, command=nova_despesa, image=img_add_despesas, compound=LEFT, anchor=NW, text=" Adicionar".upper(), width=80, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_inserir_despesa.place(x=160, y=171)

# Botao Atualizar despesas
img_update_despesas  = Image.open('imagens/atualizar.png')
img_update_despesas = img_update_despesas.resize((17,17))
img_update_despesas = ImageTk.PhotoImage(img_update_despesas)
botao_atualizar_despesa = Button(frame_despesas, command=atualizar, image=img_update_despesas, compound=LEFT, anchor=NW, text=" Atualizar".upper(), width=80, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_atualizar_despesa.place(x=55, y=171)

l_n_categoria = Label(frame_despesas, text="Categoria", height=1,anchor=NW, font=('Ivy 10 bold'), bg=co1, fg=co4)
l_n_categoria.place(x=55, y=230)
e_categoria = Entry(frame_despesas, width=14, justify='left',relief="solid")
e_categoria.place(x=160, y=231)

# Botao Inserir Categoria
img_add_categoria  = Image.open('imagens/add.png')
img_add_categoria = img_add_categoria.resize((17,17))
img_add_categoria = ImageTk.PhotoImage(img_add_categoria)
botao_inserir_categoria = Button(frame_despesas, command=nova_categoria, image=img_add_categoria, compound=LEFT, anchor=NW, text=" Adicionar".upper(), width=80, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_inserir_categoria.place(x=160, y=260)

# Botao remover Categoria
img_del_categoria  = Image.open('imagens/delete.png')
img_del_categoria = img_del_categoria.resize((17,17))
img_del_categoria = ImageTk.PhotoImage(img_del_categoria)
botao_remover_categoria = Button(frame_despesas, command=remover_categoria, image=img_del_categoria, compound=LEFT, anchor=NW, text=" Remover".upper(), width=80, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_remover_categoria.place(x=55, y=260)

# Interface receitas ----------------------------------------------------------

l_head_receita = Label(frame_receitas, text="INSIRA NOVAS RECEITAS", height=1,anchor=NW,relief="flat", font=('Verdana 10 bold'), bg=co1, fg=co4)
l_head_receita.place(x=55, y=10)

l_descrição_receita = Label(frame_receitas, text="Descrição", height=1,anchor=NW, font=('Ivy 10 '), bg=co1, fg=co4)
l_descrição_receita.place(x=55, y=50)
e_descrição_receita = Entry(frame_receitas, width=14, justify='left',relief="solid")
e_descrição_receita.place(x=160, y=51)

l_cal_receitas = Label(frame_receitas, text="Data", height=1,anchor=NW, font=('Ivy 10 '), bg=co1, fg=co4)
l_cal_receitas.place(x=55, y=80)
e_cal_receitas = DateEntry(frame_receitas, locale='pt_BR', date_pattern='dd/MM/yyyy', width=12, background='darkblue', foreground='white', borderwidth=2)
e_cal_receitas.place(x=160, y=81)

l_valor_receitas = Label(frame_receitas, text="Valor (R$)", height=1,anchor=NW, font=('Ivy 10 '), bg=co1, fg=co4)
l_valor_receitas.place(x=55, y=110)
e_valor_receitas = Entry(frame_receitas, width=14, justify='left',relief="solid")
e_valor_receitas.place(x=160, y=111)

# Botao Inserir receitas
img_add_receitas  = Image.open('imagens/add.png')
img_add_receitas = img_add_receitas.resize((17,17))
img_add_receitas = ImageTk.PhotoImage(img_add_receitas)
botao_inserir_receita = Button(frame_receitas, command=nova_receita, image=img_add_receitas, compound=LEFT, anchor=NW, text=" Adicionar".upper(), width=80, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_inserir_receita.place(x=160, y=141)

# # Botao Atualizar receitas
img_update_receita  = Image.open('imagens/atualizar.png')
img_update_receita = img_update_receita.resize((17,17))
img_update_receita = ImageTk.PhotoImage(img_update_receita)
botao_atualizar_receita = Button(frame_receitas, command=atualizar, image=img_update_receita, compound=LEFT, anchor=NW, text=" Atualizar".upper(), width=80, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_atualizar_receita.place(x=55, y=141)


# Interface extratos ----------------------------------------------------------------

l_head_extratos = Label(frame_extrato, text="INSIRA NOVAS EXTRATOS", height=1,anchor=NW,relief="flat", font=('Verdana 10 bold'), bg=co1, fg=co4)
l_head_extratos.place(x=55, y=10)
# Botão para pesquisa de arquivo
botao_pesquisar = Button(frame_extrato, text="PESQUISAR", command=pesquisar_arquivo, compound=LEFT, anchor=NW, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_pesquisar.place(x=10, y=51)
# Label para exibir o resultado da pesquisa
label_resultado = Label(frame_extrato, text="")
label_resultado.place(x=80, y=50)

# Radiobuttons extratos
selecionado = StringVar()
radio_conta = Radiobutton(frame_extrato, text='Conta', var=selecionado, value='conta', overrelief=RIDGE, font=('ivy 7 bold'),bg=co1, fg=co0 )
radio_conta.place(x=10, y=82)
radio_credito = Radiobutton(frame_extrato, text='Credito', var=selecionado, value='credito', overrelief=RIDGE, font=('ivy 7 bold'),bg=co1, fg=co0 )
radio_credito.place(x=70, y=82)
radio_sodexo = Radiobutton(frame_extrato, text='Sodexo', var=selecionado, value='sodexo', overrelief=RIDGE, font=('ivy 7 bold'),bg=co1, fg=co0 )
radio_sodexo.place(x=137, y=82)

img_confirm  = Image.open('imagens/verifica.png')
img_confirm = img_confirm.resize((17,17))
img_confirm = ImageTk.PhotoImage(img_confirm)
botao_confirmar = Button(frame_extrato, command=confirmar_extrato, image=img_confirm, compound=LEFT, anchor=NW, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_confirmar.place(x=255, y=80)

# Interface configurações ----------------------------------------------------------------

l_head_config = Label(frame_config, text="CONFIGURAÇÕES", height=1,anchor=NW,relief="flat", font=('Verdana 10 bold'), bg=co1, fg=co4)
l_head_config.place(x=85, y=10)


# operacao selecionar periodo de tempo
l_periodo = Label(frame_config, text="Periodo", height=1,anchor=NW, font=('Ivy 10 bold'), bg=co1, fg=co4)
l_periodo.place(x=10, y=50)

l_cal_periodo_inicio = Label(frame_config, text="Inicio", height=1,anchor=NW, font=('Ivy 10 '), bg=co1, fg=co4)
l_cal_periodo_inicio.place(x=10, y=80)
e_cal_periodo_inicio = DateEntry(frame_config, locale='pt_BR', date_pattern='dd/MM/yyyy', width=12, background='darkblue', foreground='white', borderwidth=2)
e_cal_periodo_inicio.place(x=52, y=81)

l_cal_periodo_fim = Label(frame_config, text="Fim", height=1,anchor=NW, font=('Ivy 10 '), bg=co1, fg=co4)
l_cal_periodo_fim.place(x=10, y=110)
e_cal_periodo_fim = DateEntry(frame_config, locale='pt_BR', date_pattern='dd/MM/yyyy', width=12, background='darkblue', foreground='white', borderwidth=2)
e_cal_periodo_fim.place(x=52, y=111)

botao_confirmar_periodo = Button(frame_config, command=confirmar_periodo, image=img_confirm, compound=LEFT, anchor=NW, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_confirmar_periodo.place(x=120, y=50)

# operacao selecionar fechamento e pagamento do cartao de credito
l_credito = Label(frame_config, text="Cartão de Credito", height=1,anchor=NW, font=('Ivy 10 bold'), bg=co1, fg=co4)
l_credito.place(x=150, y=50)

l_cal_credito_fechamento = Label(frame_config, text="Fecha", height=1,anchor=NW, font=('Ivy 10 '), bg=co1, fg=co4)
l_cal_credito_fechamento.place(x=150, y=80)
e_cal_credito_fechamento = DateEntry(frame_config, locale='pt_BR', date_pattern='dd/MM/yyyy', width=12, background='darkblue', foreground='white', borderwidth=2)
e_cal_credito_fechamento.place(x=200, y=81)

l_cal_credito_pagamento = Label(frame_config, text="Paga", height=1,anchor=NW, font=('Ivy 10 '), bg=co1, fg=co4)
l_cal_credito_pagamento.place(x=150, y=110)
e_cal_credito_pagamento = DateEntry(frame_config, locale='pt_BR', date_pattern='dd/MM/yyyy', width=12, background='darkblue', foreground='white', borderwidth=2)
e_cal_credito_pagamento.place(x=200, y=111)

botao_confirmar_credito = Button(frame_config, image=img_confirm, compound=LEFT, anchor=NW, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_confirmar_credito.place(x=270, y=50)

# operacao Excluir linha
l_excluir = Label(frame_config, text="Excluir linha", height=1,anchor=NW, font=('Ivy 10 bold'), bg=co1, fg=co4)
l_excluir.place(x=35, y=150)

# Botao excluir
img_delete  = Image.open('imagens/delete.png')
img_delete = img_delete.resize((20, 20))
img_delete = ImageTk.PhotoImage(img_delete)
botao_excluir = Button(frame_config, command=deletar, image=img_delete, compound=LEFT, anchor=NW, text="   Excluir".upper(), width=80, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_excluir.place(x=35, y=180)

# operacao Reiniciar planilha
l_reiniciar = Label(frame_config, text="Reiniciar planilha", height=1,anchor=NW, font=('Ivy 10 bold'), bg=co1, fg=co4)
l_reiniciar.place(x=150, y=150)

# Botao reset
img_reset  = Image.open('imagens/atualizar.png')
img_reset = img_reset.resize((20, 20))
img_reset = ImageTk.PhotoImage(img_reset)
botao_reset = Button(frame_config, command=reiniciar_dados, image=img_reset, compound=LEFT, anchor=NW, text="   Reiniciar".upper(), width=80, overrelief=RIDGE,  font=('ivy 7 bold'),bg=co1, fg=co0 )
botao_reset.place(x=163, y=180)

# Checkbutton reset
estado = BooleanVar()
check_reset = Checkbutton(frame_config, text='Confirmar', var=estado, onvalue=1, offvalue=0, overrelief=RIDGE, font=('ivy 7 bold'),bg=co1, fg=co0 )
check_reset.place(x=168, y=210)

def atualizar_interface():
    mostrar_tabela()
    grafico_pie()
    porcentagem()
    resumo()


atualizar_interface()



janela.mainloop()