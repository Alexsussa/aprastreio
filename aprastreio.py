#!/usr/bin/python3
# -*- encoding: utf-8 -*-

__version__ = 1.0

from tkinter.ttk import *
from tkinter.messagebox import *
from tkinter.filedialog import *
from tkinter import *
from bs4 import BeautifulSoup
from urllib.request import urlopen
from mailcomposer import MailComposer
from threading import Thread
from multiprocessing import Process
import os
import sys
import sqlite3
import webbrowser
import ttips
import subprocess
import socket

listaRastreio = []

listaObjeto = []

db = os.path.expanduser('~/Dropbox/aprastreio/banco/')
if not os.path.exists(db):
    os.path.join(os.mkdir(db), 'rastreios.db')
else:
    banco = os.path.join(os.path.dirname(db), 'rastreios.db')
    conexao = sqlite3.connect(banco, check_same_thread=False)
    c = conexao.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS rastreio (id INTEGER PRIMARY KEY AUTOINCREMENT,'
              'codrastreio TEXT VARCHAR(13) UNIQUE NOT NULL, objeto TEXT VARCHAR(50) NOT NULL)')


def CheckUpdates(event=None):
    janela.unbind('<Enter>')
    versao = urlopen('https://www.dropbox.com/s/61rpf1xg8qr1vh1/version_linux.txt?dl=true').read()
    if float(versao) > float(__version__):
        subprocess.call(
            ['notify-send', 'AP - Rastreio Correios', 'Há uma nova versão disponível. Baixe agora!'])
        info = showinfo(title='Atualização', message='Há uma nova versão disponível. Baixe agora!')
        webbrowser.open('https://github.com/Alexsussa/aprastreio/releases/')


class Rastreio(object):
    def __init__(self, master=None, rastreio='', objeto=''):

        self.rastreio = rastreio
        self.objeto = objeto

        self.c1 = Frame(master)
        self.c1['padx'] = 5
        self.c1['pady'] = 3
        self.c1.pack()

        self.c2 = Frame(master)
        self.c2.pack()

        self.c3 = Frame(master)
        self.c3.pack()

        self.c4 = Frame(master)
        self.c4.pack()

        self.c5 = Frame(master)
        self.c5.pack()

        self.lbRastreio = Label(self.c1, text='RASTREIO:', fg='black')
        self.lbRastreio.pack(side=LEFT)
        self.txtRastreio = Entry(self.c1, width=15, bg='white', fg='black', selectbackground='blue',
                                 selectforeground='white')
        self.txtRastreio.pack(side=LEFT, padx=2)

        self.lbObjeto = Label(self.c1, text='OBJETO:', fg='black')
        self.lbObjeto.pack(side=LEFT)
        self.txtObjeto = Combobox(self.c1, width=30, background='white', foreground='black',
                                  values=self.ListaObjetos(event='<Button-1>'))
        self.txtObjeto.pack(side=LEFT, padx=2)
        janela.bind('<<ComboboxSelected>>', self.Busca)

        self.btnRastrear = Button(self.c1, text='RASTREAR', fg='black',
                                  command=lambda: {Thread(target=self.Rastrear).start(), self.BuscaRastreio()})
        self.btnRastrear.pack(side=LEFT, padx=2)
        janela.bind('<Return>', self.BuscaRastreio)
        janela.bind('<Return>', self.Rastrear, self.BuscaRastreio)
        janela.bind('<KP_Enter>', self.BuscaRastreio)
        janela.bind('<KP_Enter>', self.Rastrear, self.BuscaRastreio)

        self.campo = Text(self.c2, width=77, height=30, bg='lightgray', fg='black', state='disable',
                          selectbackground='blue', font=('sans-serif', '10'))
        self.campo.pack(fill='both', expand=True, pady=5)

        self.whatsappimg = PhotoImage(file='imagens/WhatsApp.png')
        self.emailimg = PhotoImage(file='imagens/Email.png')
        self.salvarimg = PhotoImage(file='imagens/Salvar.png')
        self.atualizarimg = PhotoImage(file='imagens/Atualizar.png')
        self.deletarimg = PhotoImage(file='imagens/Lixeira.png')

        self.btnWhatsapp = Button(image=self.whatsappimg, command=lambda: Thread(target=self.WhatsApp).start())
        self.btnWhatsapp.pack(side=RIGHT)
        ttips.Create(self.btnWhatsapp, text='Enviar por WhatsApp')

        self.btnEmail = Button(image=self.emailimg, command=lambda: Thread(target=self.Email).start())
        self.btnEmail.pack(side=RIGHT)
        ttips.Create(self.btnEmail, text='Enviar por Email')

        self.btnSalvar = Button(image=self.salvarimg, command=lambda: [self.RastreioExiste(), self.Cadastrar()])
        self.btnSalvar.pack(side=LEFT, padx=1)
        ttips.Create(self.btnSalvar, text='Salvar')

        self.btnAtualizar = Button(image=self.atualizarimg, command=self.Atualizar)
        self.btnAtualizar.pack(side=LEFT, padx=1)
        ttips.Create(self.btnAtualizar, text='Atualizar')

        self.btnDeletar = Button(image=self.deletarimg, command=self.Deletar)
        self.btnDeletar.pack(side=LEFT, padx=1)
        ttips.Create(self.btnDeletar, text='Deletar')

        self.lbCreditos = Label(text='AP Correios - 2020')
        self.lbCreditos.pack(side=TOP)

        self.lbCreditos = Label(text='Software criado por Alex Pinheiro')
        self.lbCreditos.pack(side=BOTTOM)

        self.mouseMenu = Menu(janela, tearoff=0)
        self.mouseMenu.add_command(label='Recortar')
        self.mouseMenu.add_command(label='Copiar')
        self.mouseMenu.add_command(label='Colar')
        janela.bind('<Button-3><ButtonRelease-3>', self.MenuMouse)

        janela.bind('<Control-l>', self.Limpar)
        janela.bind('<Control-L>', self.Limpar)
        janela.bind('<Enter>', Thread(target=CheckUpdates).start())

        janela.bind('<Control-a>', self.NotifAltStatus)
        janela.bind('<Control-A>', self.NotifAltStatus)
        janela.after(1800000, lambda: Thread(target=self.NotifAltStatus).start())

    def NotifAltStatus(self, event=None):
        try:
            info = showinfo(title='ATUALIZANDO RASTREIOS',
                            message='Atualizando status dos rastreios. Por favor, aguarde...',
                            detail='Clique em OK e aguarde até esta janela se fechar.\nTodos os objetos não entregues aparecerão na tela principal.')
            rastreio = self.txtRastreio.get()
            objeto = self.txtObjeto.get()
            c.execute('SELECT * FROM rastreio ORDER BY codrastreio')
            self.Limpar()
            for cod in c:
                linkcorreios = urlopen(f'https://www.linkcorreios.com.br/?id={cod[1]}')
                soup = BeautifulSoup(linkcorreios, 'html.parser')
                lastStatus = soup.find('ul', attrs={'class': 'linha_status'})
                last = lastStatus.text.strip().upper()
                self.campo.delete(1.0, END)
                if last[0:39] != 'STATUS: OBJETO ENTREGUE AO DESTINATÁRIO':
                    self.campo.config(state='normal')
                    self.campo.insert(INSERT, '-' * 80)
                    self.campo.insert(INSERT, '\n\nALTERAÇÃO DE STATUS')
                    self.campo.insert(INSERT, f'\n\n{cod[2]}\n{cod[1]}\n\n{last}\n\n', '-' * 80)
                    self.campo.config(state='disable')
                    subprocess.call(
                        ['notify-send', 'AP - Rastreio Correios', f'ALTERAÇÂO DE STATUS\n\n{cod[2]}\n\n{last}\n\n'])

        except:
                subprocess.call(['notify-send', 'AP - Rastreio Correios',
                                 'Tempo de resposta do servidor execedido.\n\nSem conexão com a internet.'])
                showerror(title='AVISO',
                          message='Tempo de resposta do servidor execedido.\n\nSem conexão com a internet.')

    def MenuMouse(self, event):
        w = event.widget
        self.mouseMenu.entryconfigure("Recortar", command=lambda: w.event_generate('<<Cut>>'))
        self.mouseMenu.entryconfigure("Copiar", command=lambda: w.event_generate('<<Copy>>'))
        self.mouseMenu.entryconfigure("Colar", command=lambda: w.event_generate('<<Paste>>'))
        self.mouseMenu.tk_popup(event.x_root, event.y_root)

    def Rastrear(self, event=None):
        rastreio = self.txtRastreio.get()
        objeto = self.txtObjeto.get()
        if rastreio == '':
            aviso = showwarning(title='AVISO', message='Digite um código de rastreio para rastrear.')

        elif len(rastreio) != 13:
            aviso = showwarning(title='AVISO', message='Rastreio deve conter 13 dígitos\nsendo duas letras iniciais e '
                                                       'duas letras finais, como no\nexemplo abaixo:\n\n "OJ123456789BR"')

        else:
            try:
                subprocess.call(['notify-send', 'AP - Rastreio Correios', 'Rastreando encomenda...'])
                linkcorreios = urlopen(f'https://www.linkcorreios.com.br/?id={rastreio}', timeout=20)
                soup = BeautifulSoup(linkcorreios, 'html.parser')
                status = soup.find('div', attrs={'class': 'singlepost'})
                retorno = ''
                if status:
                    retorno = status.text.strip().upper()
                else:
                    retorno = 'O rastreamento não está disponível no momento:\n\n' \
                              '- Verifique se o código do objeto está correto;\n' \
                              '- O objeto pode demorar até 24 horas (após postagem) para ser rastreado no\nsistema dos Correios.'.strip().upper()
                # print(retorno)
                self.campo.config(state='normal')
                self.campo.delete(1.0, END)
                self.campo.insert(INSERT, retorno)
                self.campo.config(state='disable')
                lastStatus = soup.find('ul', attrs={'class': 'linha_status'})
                if lastStatus:
                    last = lastStatus.text.strip().upper()
                else:
                    last = 'O rastreamento não está disponível no momento:\n\n' \
                           '- Verifique se o código do objeto está correto;\n' \
                           '- O objeto pode demorar até 24 horas (após postagem) para ser rastreado no sistema dos Correios.'.strip().upper()
                subprocess.call(['notify-send', 'AP - Rastreio Correios', f'{objeto}\n\n{last}'])

            except socket.error:
                subprocess.call(['notify-send', 'AP - Rastreio Correios',
                                 'Tempo de resposta do servidor execedido.\n\nSem conexão com a internet.'])
                showerror(title='AVISO',
                          message='Tempo de resposta do servidor execedido.\n\nSem conexão com a internet.')

            """except socket.timeout:
                subprocess.call(
                    ['notify-send', 'AP - Rastreio Correios', 'Tempo de resposta do servidor execedido.'])
                showerror(title='AVISO', message='Tempo de resposta do servidor execedido.')"""

    def WhatsApp(self):
        rastreio = self.txtRastreio.get().strip().upper()

        if rastreio == '':
            erro = showerror(title='AVISO', message='Para fazer o envio pelo WhatsApp, primeiro busque pelo rastreio.')

        elif len(rastreio) != 13:
            aviso = showwarning(title='AVISO', message='Rastreio deve conter 13 dígitos\nsendo duas letras iniciais e '
                                                       'duas letras finais, como no\nexemplo abaixo:\n\n "OJ123456789BR"')

        else:
            rastreio = self.txtRastreio.get()
            webbrowser.open(
                f'https://web.whatsapp.com/send?phone=&text=Ol%c3%a1.%20Clique%20no%20link%20para%20rastrear%20o%20objeto%20c%c3%b3digo%20{rastreio}%0ahttps%3a%2f%2fwww.linkcorreios.com.br%2f{rastreio}%3fw%3d1&source=&data=')

    def Email(self):
        if not os.path.exists('/usr/bin/thunderbird') and not os.path.exists('/usr/bin/evolution'):
            aviso = showwarning(title='AVISO', message='Nenhum cliente de email está instalado em seu computador.')
        else:
            rastreio = self.txtRastreio.get().strip().upper()

        if rastreio == '':
            erro = showerror(title='AVISO', message='Para fazer o envio pelo Email, primeiro busque pelo rastreio.')

        elif len(rastreio) != 13:
            aviso = showwarning(title='AVISO', message='Rastreio deve conter 13 dígitos\nsendo duas letras iniciais e '
                                                       'duas letras finais, como no\nexemplo abaixo:\n\n "OJ123456789BR"')

        else:
            mc = MailComposer()
            rastreio = self.txtRastreio.get()
            mc.subject = f'Código de Rastreio ({rastreio})'
            mc.body = f'Boa tarde!\n\n Segue código de rastreio para acompanhamento do seu pedido:\n\n https://www.linkcorreios.com.br/?id={rastreio}.\n\n'
            mc.display('Megatecshop - Rastreio Correios')
            # webbrowser.open(f'https://www.linkcorreios.com.br/?id={rastreio}#envie_por_email')

    def Cadastrar(self):
        rastreio = self.txtRastreio.get().strip().upper()

        if self.txtRastreio.get() == '' or self.txtObjeto.get() == '':
            aviso = showwarning(title='AVISO', message='Nenhum campo pode estar vazio.')

        elif len(rastreio) != 13:
            aviso = showwarning(title='AVISO', message='Rastreio deve conter 13 dígitos\nsendo duas letras iniciais e '
                                                       'duas letras finais, como no\nexemplo abaixo:\n\n "OJ123456789BR"')

        else:
            rastreio = self.txtRastreio.get().strip().upper()
            objeto = self.txtObjeto.get().strip().upper()
            c.execute(f'INSERT INTO rastreio (codrastreio, objeto) VALUES ("{rastreio}", "{objeto}")')
            conexao.commit()

            self.txtRastreio.delete(0, END)
            self.txtObjeto.delete(0, END)
            listaObjeto.clear()
            self.txtObjeto.config(values=self.ListaObjetos())

            status = showinfo(title='STATUS', message=f'Rastreio {rastreio} cadastrado com sucesso.')

    def Atualizar(self):
        rastreio = self.txtRastreio.get().strip().upper()
        objeto = self.txtObjeto.get().strip().upper()

        if self.txtRastreio.get() == '' or self.txtObjeto.get() == '':
            status = showerror(title='AVISO', message='Para atualizar os dados procure pelo rastreio primeiro.')

        else:
            aviso = askyesno(title='AVISO', message='Você deseja atualizar os dados desse rastreio?')

            if aviso == False:
                pass

            elif aviso == True:
                c.execute(
                    f'UPDATE rastreio SET codrastreio = "{rastreio}", objeto = "{objeto}" WHERE codrastreio = "{rastreio}"')
                conexao.commit()

                self.txtRastreio.delete(0, END)
                self.txtObjeto.delete(0, END)
                listaObjeto.clear()
                self.txtObjeto.config(values=self.ListaObjetos())

                status = showinfo(title='STATUS', message=f'Rastreio {rastreio} atualizado com sucesso.')

            else:
                return None

    def Deletar(self):
        rastreio = self.txtRastreio.get().strip().upper()

        if self.txtRastreio.get() == '' or self.txtObjeto.get() == '':
            status = showerror(title='AVISO', message='Para deletar os dados procure pelo rastreio primeiro.')

        else:
            aviso = askyesno(title='AVISO', message='Você realmente deseja DELETAR os dados desse rastreio?\n'
                                                    'Esta ação não poderá ser desfeita.')

            if aviso == False:
                pass

            elif aviso == True:
                c.execute(f'DELETE FROM rastreio WHERE codrastreio = "{rastreio}"')
                conexao.commit()

                self.txtRastreio.delete(0, END)
                self.txtObjeto.delete(0, END)
                listaObjeto.clear()
                self.txtObjeto.config(values=self.ListaObjetos())

                status = showinfo(title='STATUS', message=f'Rastreio {rastreio} deletado com sucesso.')

            else:
                return None

    def ListaObjetos(self, event=None):
        c.execute(f'SELECT objeto FROM rastreio ORDER BY id')
        for objeto in c:
            if objeto[0] not in listaObjeto:
                listaObjeto.append(objeto[0])
        return tuple(reversed(listaObjeto))

    def ListaRastreio(self, event=None):
        c.execute(f'SELECT codrastreio FROM rastreio ORDER BY codrastreio')
        for rastreio in c:
            if rastreio[0] not in listaRastreio:
                listaRastreio.append(rastreio[0])
        return tuple(listaRastreio)

    def Busca(self, event=None):
        objeto = self.txtObjeto.get().strip().upper()
        c.execute(f'SELECT * FROM rastreio WHERE objeto = "{objeto}"')

        for linha in c:
            self.rastreio = linha[1]
            self.objeto = linha[2]

            self.txtRastreio.delete(0, END)
            self.txtRastreio.insert(INSERT, self.rastreio)
            self.txtObjeto.delete(0, END)
            self.txtObjeto.insert(INSERT, self.objeto)

    def BuscaRastreio(self, event=None):
        rastreio = self.txtRastreio.get().strip().upper()
        c.execute(f'SELECT * FROM rastreio WHERE codrastreio = "{rastreio}"')

        for linha in c:
            self.rastreio = linha[1]
            self.objeto = linha[2]

            self.txtRastreio.delete(0, END)
            self.txtRastreio.insert(INSERT, self.rastreio)
            self.txtObjeto.delete(0, END)
            self.txtObjeto.insert(INSERT, self.objeto)

    def RastreioExiste(self):
        rastreio = self.txtRastreio.get().strip().upper()
        c.execute(f'SELECT * FROM rastreio WHERE codrastreio = "{rastreio}"')
        for item in c:
            if rastreio == item[1]:
                status = showinfo(title='STATUS',
                                  message='Código já cadastrado.\nTecle ENTER para\nbuscar o nome do objeto.')

    def Limpar(self, event=None):
        self.campo.config(state='normal')
        self.txtRastreio.delete(0, END)
        self.txtObjeto.delete(0, END)
        self.campo.delete(1.0, END)
        self.campo.config(state='disable')


janela = Tk()
iconejanela = PhotoImage(file='imagens/iconejanela.png')
janela.tk.call('wm', 'iconphoto', janela._w, iconejanela)
janela.resizable(False, False)
janela.geometry('630x610')
Rastreio(janela)
janela.title('AP - RASTREIO CORREIOS v1.0')
janela.update()
janela.after(1800000, CheckUpdates)
janela.mainloop()
