#!/usr/bin/python3
# -*- encoding: utf-8 -*-

__version__ = 1.3

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from bs4 import BeautifulSoup
from urllib.request import urlopen
from mailcomposer import MailComposer
from threading import Thread
import os
import sys
import sqlite3
import webbrowser
import subprocess
import socket

listaRastreio = []

listaObjeto = []

pid = str(os.getpid())
pidfile = os.path.join('/tmp/aprastreio.pid')
if not os.path.isfile(pidfile):
    os.system(f'touch {pidfile}')
    os.system(f'echo {pid} >> {pidfile}')
else:
    sys.exit(-1)

# Cria o banco de dados caso ele não exista
db = os.path.expanduser('~/Dropbox/aprastreio/banco/')
if not os.path.exists(db):
    os.makedirs(db)
    banco = os.path.join(os.path.dirname(db), 'rastreios.db')
    conexao = sqlite3.connect(banco, check_same_thread=False)
    c = conexao.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS rastreio (id INTEGER PRIMARY KEY AUTOINCREMENT,'
              'codrastreio TEXT VARCHAR(13) UNIQUE NOT NULL, objeto TEXT VARCHAR(50) NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS entregues (id INTEGER PRIMARY KEY AUTOINCREMENT,'
              'codrastreio TEXT VARCHAR(13) UNIQUE NOT NULL, objeto TEXT VARCHAR(50) NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS pendentes (id INTEGER PRIMARY KEY AUTOINCREMENT,'
              'codrastreio TEXT VARCHAR(13) UNIQUE NOT NULL, objeto TEXT VARCHAR(50) NOT NULL)')
else:
    banco = os.path.join(os.path.dirname(db), 'rastreios.db')
    conexao = sqlite3.connect(banco, check_same_thread=False)
    c = conexao.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS rastreio (id INTEGER PRIMARY KEY AUTOINCREMENT,'
              'codrastreio TEXT VARCHAR(13) UNIQUE NOT NULL, objeto TEXT VARCHAR(50) NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS entregues (id INTEGER PRIMARY KEY AUTOINCREMENT,'
              'codrastreio TEXT VARCHAR(13) UNIQUE NOT NULL, objeto TEXT VARCHAR(50) NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS pendentes (id INTEGER PRIMARY KEY AUTOINCREMENT,'
              'codrastreio TEXT VARCHAR(13) UNIQUE NOT NULL, objeto TEXT VARCHAR(50) NOT NULL)')


class Rastreio:
    def __init__(self):
        self.txtRastreio = builder.get_object('txtRastreio')
        self.txtObjeto = builder.get_object('txtObjeto')
        self.txtCampo = builder.get_object('txtCampo')
        self.txtcampobuffer = builder.get_object('txtbuffer')
        self.rolagem_vertical = builder.get_object('rolvertical')
        self.liObjeto = builder.get_object('liObjeto')
        self.janErro = builder.get_object('janErro')
        self.janInfo = builder.get_object('janInfo')
        self.janPergunta = builder.get_object('janPergunta')
        self.janPerguntaAtt = builder.get_object('janPerguntaAtt')
        self.pergAttRastreios = builder.get_object('pergAttRastreios')
        self.sobre = builder.get_object('sobre')
        self.btnNovaAtt = builder.get_object('btnNovaAtt')
        self.sobre.connect('response', lambda d, r: d.hide())

        Thread(target=self.checkUpdates).start()

        c.execute(f'SELECT objeto FROM rastreio ORDER BY id')
        for objeto in c:
            if objeto[0] not in self.liObjeto:
                self.liObjeto.prepend_text(objeto[0])
                self.liObjeto.set_active(-1)

    # Procura novas versões do software
    def checkUpdates(self, event=None):
        versao = urlopen('https://www.dropbox.com/s/61rpf1xg8qr1vh1/version_linux.txt?dl=true').read()
        if float(versao) > float(__version__):
            subprocess.call(
                ['notify-send', 'AP - Rastreio Correios',
                 'Há uma nova versão disponível. Clique em ajuda no menu superior e baixe agora!'])
            self.btnNovaAtt.set_sensitive(True)

    def on_btnNovaAtt_activate(self, button):
        Thread(target=webbrowser.open('https://github.com/Alexsussa/aprastreio/releases/')).start()

    def on_btnChecarAtt_activate(self, button):
        self.checkUpdates()

    def on_btnSair_activate(self, button):
        self.on_aprastreio_destroy(window=None)

    def NotifAltStatus(self, event=None):
        self.pergAttRastreios.show()
        self.pergAttRastreios.set_markup(
            '\n\nAtualizando status dos rastreios...\nClique em SIM e aguarde até os objetos não entregues aparecerem na tela principal\nou clique em NÃO para atualizar manualmente mais tarde.')

    def on_btnAttSim_clicked(self, button):
        self.pergAttRastreios.hide()
        subprocess.call(['notify-send', 'AP - Rastreio Correios',
                         'Atualizando status dos rastreios...\n\nPor favor, aguarde...'])
        c.execute('SELECT * FROM rastreio ORDER BY codrastreio')
        try:
            for cod in c:
                linkcorreios = urlopen(f'https://www.linkcorreios.com.br/?id={cod[1]}')
                soup = BeautifulSoup(linkcorreios, 'html.parser')
                lastStatus = soup.find('ul', attrs={'class': 'linha_status'})
                last = lastStatus.text.strip().upper()
                self.txtcampobuffer.set_text(last)
                if last[0:39] != 'STATUS: OBJETO ENTREGUE AO DESTINATÁRIO':
                    self.txtCampo.set_buffer(self.txtcampobuffer)
                    self.txtcampobuffer.set_text('-' * 80)
                    self.txtcampobuffer.set_text('\n\nALTERAÇÃO DE STATUS')
                    self.txtcampobuffer.set_text(f'\n\n{cod[2]}\n{cod[1]}\n\n{last}\n\n', '-' * 80)
                    subprocess.call(
                        ['notify-send', 'AP - Rastreio Correios', f'ALTERAÇÂO DE STATUS\n\n{cod[2]}\n\n{last}\n\n'])
            subprocess.call(['notify-send', 'AP - Rastreio Correios',
                             'Todos os objetos não entregues estão na tela principal.'])

        except socket.error:
            subprocess.call(['notify-send', 'AP - Rastreio Correios',
                             'Tempo de resposta do servidor execedido.\n\nSem conexão com a internet.'])
            self.janErro.show()
            self.janErro.set_markup('\n\nTempo de resposta do servidor execedido.\n\nSem conexão com a internet.')

    def on_btnAttNão_clicked(self, button):
        self.pergAttRastreios.hide()

    def on_sincRastreios_activate(self, button):
        self.NotifAltStatus()

    def on_liObjeto_changed(self, button):
        objeto = self.txtObjeto.get_text().strip().upper()
        c.execute(f'SELECT * FROM rastreio WHERE objeto = "{objeto}"')
        for item in c:
            self.txtRastreio.set_text(item[1])
            self.txtObjeto.set_text(item[2])
        c.execute(f'SELECT * FROM entregues WHERE objeto = "{objeto}"')
        for item in c:
            self.txtRastreio.set_text(item[1])
            self.txtObjeto.set_text(item[2])

    def on_btnRastrear_clicked(self, button):
        Thread(target=self.rastrear).start()

    def rastrear(self):
        rastreio = self.txtRastreio.get_text()
        # objeto = self.txtObjeto.get_text()
        if self.txtRastreio.get_text() == '':
            self.janInfo.show()
            self.janInfo.set_markup('\n\nDigite um código de rastreio para buscar as informações.')
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
                # retorno = status.text.strip().upper()
                # print(retorno)
                self.txtCampo.set_buffer(self.txtcampobuffer)
                self.txtcampobuffer.set_text(retorno)
                lastStatus = soup.find('ul', attrs={'class': 'linha_status'})
                last = lastStatus.text.strip().upper()
                subprocess.call(['notify-send', 'AP - Rastreio Correios', f'{last}'])

            except socket.timeout:
                subprocess.call(
                    ['notify-send', 'AP - Rastreio Correios', 'Tempo de resposta do servidor execedido.'])
                self.janErro.show()
                self.janErro.set_markup('\n\nTempo de resposta do servidor execedido.')

            except socket.error:
                subprocess.call(['notify-send', 'AP - Rastreio Correios', 'Sem conexão com a internet.'])
                self.janErro.show()
                self.janErro.set_markup('\n\nSem conexão com a internet.')

    def on_btnErroOk_clicked(self, button):
        self.janErro.hide()

    def on_btnSalvar_clicked(self, button):
        rastreio = self.txtRastreio.get_text().strip().upper()
        if self.txtRastreio.get_text() == '' or self.txtObjeto.get_text() == '':
            self.janInfo.show()
            self.janInfo.set_markup('\n\nPara salvar digite o rastreio e o nome do objeto.')

        elif len(rastreio) != 13:
            self.janInfo.show()
            self.janInfo.set_markup('\n\nRastreio deve conter 13 dígitos\nsendo duas letras iniciais e '
                                    'duas letras finais, como no\nexemplo abaixo:\n\n "OJ123456789BR"')

        else:
            rastreio = self.txtRastreio.get_text().strip().upper()
            objeto = self.txtObjeto.get_text().strip().upper()
            c.execute(f'INSERT INTO rastreio (codrastreio, objeto) VALUES ("{rastreio}", "{objeto}")')
            conexao.commit()

            self.txtRastreio.set_text('')
            self.txtObjeto.set_text('')
            self.liObjeto.prepend_text(objeto)
            self.liObjeto.set_active(-1)

            self.janInfo.show()
            self.janInfo.set_markup(f'\n\nRastreio {rastreio} cadastrado com sucesso.')

    def on_btnJanInfo_clicked(self, button):
        self.janInfo.hide()

    def on_btnAtualizar_clicked(self, button):
        if self.txtRastreio.get_text() == '' or self.txtObjeto.get_text() == '':
            self.janInfo.show()
            self.janInfo.set_markup('\n\nPara atualizar os dados procure pelo rastreio primeiro.')

        else:
            self.janPerguntaAtt.show()
            self.janPerguntaAtt.set_markup('\n\nVocê deseja atualizar os dados desse rastreio?')

    def on_btnPerguntaAttNão_clicked(self, button):
        self.janPerguntaAtt.hide()

    def on_btnPerguntaAttSim_clicked(self, button):
        rastreio = self.txtRastreio.get_text().strip().upper()
        objeto = self.txtObjeto.get_text().strip().upper()
        self.janPerguntaAtt.hide()
        c.execute(
            f'UPDATE rastreio SET codrastreio = "{rastreio}", objeto = "{objeto}" WHERE codrastreio = "{rastreio}"')
        conexao.commit()

        self.txtRastreio.set_text('')
        self.txtObjeto.set_text('')
        self.liObjeto.remove_all()
        c.execute(f'SELECT objeto FROM rastreio ORDER BY id')
        for objeto in c:
            if objeto[0] not in self.liObjeto:
                self.liObjeto.prepend_text(objeto[0])
                self.liObjeto.set_active(-1)
        self.janInfo.show()
        self.janInfo.set_markup(f'\n\nRastreio {rastreio} atualizado com sucesso.')

    def on_btnDeletar_clicked(self, button):
        if self.txtRastreio.get_text() == '' or self.txtObjeto.get_text() == '':
            self.janErro.show()
            self.janErro('\n\nPara deletar os dados procure pelo rastreio primeiro.')

        else:
            self.janPergunta.show()
            self.janPergunta.set_markup('\n\nVocê realmente deseja DELETAR os dados desse rastreio?\n'
                                        'Esta ação não poderá ser desfeita.')

    def on_btnPerguntaNão_clicked(self, button):
        self.janPergunta.hide()

    def on_btnPerguntaSim_clicked(self, button):
        rastreio = self.txtRastreio.get_text().strip().upper()
        objeto = self.txtObjeto.get_text().strip().upper()
        self.janPergunta.hide()
        c.execute(f'DELETE FROM rastreio WHERE codrastreio = "{rastreio}"')
        conexao.commit()

        self.txtRastreio.set_text('')
        self.txtObjeto.set_text('')
        self.liObjeto.remove_all()
        c.execute(f'SELECT objeto FROM rastreio ORDER BY id')
        for objeto in c:
            if objeto[0] not in self.liObjeto:
                self.liObjeto.prepend_text(objeto[0])
                self.liObjeto.set_active(-1)
        self.janInfo.show()
        self.janInfo.set_markup(f'\n\nRastreio {rastreio} deletado com sucesso.')

    def on_btnWhatsApp_clicked(self, button):
        rastreio = self.txtRastreio.get_text().strip().upper()
        if rastreio == '':
            self.janInfo.show()
            self.janInfo.set_markup('\n\nPara fazer o envio pelo WhatsApp, primeiro busque pelo rastreio.')

        elif len(rastreio) != 13:
            self.janInfo.show()
            self.janInfo.set_markup('\n\nRastreio deve conter 13 dígitos\nsendo duas letras iniciais e '
                                    'duas letras finais, como no\nexemplo abaixo:\n\n "OJ123456789BR"')

        else:
            rastreio = self.txtRastreio.get_text()
            webbrowser.open(
                f'https://web.whatsapp.com/send?phone=&text=Ol%c3%a1.%20Clique%20no%20link%20para%20rastrear%20o%20objeto%20c%c3%b3digo%20{rastreio}%0ahttps%3a%2f%2fwww.linkcorreios.com.br%2f{rastreio}%3fw%3d1&source=&data=')

    def on_btnEmail_clicked(self, button):
        if not os.path.exists('/usr/bin/thunderbird') and not os.path.exists('/usr/bin/evolution'):
            self.janInfo.show()
            self.janInfo.set_markup('\n\nNenhum cliente de email está instalado em seu computador.')
        else:
            rastreio = self.txtRastreio.get_text().strip().upper()

        if rastreio == '':
            self.janInfo.show()
            self.janInfo.set_markup('\n\nPara fazer o envio pelo Email, primeiro busque pelo rastreio.')

        elif len(rastreio) != 13:
            self.janInfo.show()
            self.janInfo.set_markup('\n\nRastreio deve conter 13 dígitos\nsendo duas letras iniciais e '
                                    'duas letras finais, como no\nexemplo abaixo:\n\n "OJ123456789BR"')
        else:
            mc = MailComposer()
            rastreio = self.txtRastreio.get_text()
            mc.subject = f'Código de Rastreio ({rastreio})'
            mc.body = f'Boa tarde!\n\n Segue código de rastreio para acompanhamento do seu pedido:\n\n https://www.linkcorreios.com.br/?id={rastreio}.\n\n'
            mc.display('Megatecshop - Rastreio Correios')

    def on_entregues_activate(self, button):
        self.liObjeto.remove_all()
        self.txtRastreio.set_text('')
        self.txtObjeto.set_text('')
        c.execute(f'SELECT objeto FROM entregues ORDER BY id')
        for objeto in c:
            if objeto[0] not in self.liObjeto:
                self.liObjeto.prepend_text(objeto[0])
                self.liObjeto.set_active(-1)

    def on_pendentes_activate(self, button):
        self.liObjeto.remove_all()
        self.txtRastreio.set_text('')
        self.txtObjeto.set_text('')
        c.execute(f'SELECT objeto FROM rastreio ORDER BY id')
        for objeto in c:
            if objeto[0] not in self.liObjeto:
                self.liObjeto.prepend_text(objeto[0])
                self.liObjeto.set_active(-1)

    def on_btnSobre_activate(self, button):
        self.sobre.show()

    def on_moverParaEntregues_activate(self, button):
        rastreio = self.txtRastreio.get_text()
        objeto = self.txtObjeto.get_text()
        if rastreio == '' or objeto == '':
            self.janInfo.show()
            self.janInfo.set_markup('\n\nSelecione um rastreio para mover.')
        else:
            c.execute(f'SELECT codrastreio FROM rastreio WHERE codrastreio = "{rastreio}"')
            c.execute(f'INSERT INTO entregues SELECT * FROM rastreio WHERE codrastreio = "{rastreio}"')
            c.execute(f'DELETE FROM rastreio WHERE codrastreio = "{rastreio}"')
            conexao.commit()
            self.janInfo.show()
            self.janInfo.set_markup(f'\n\nRastreio {rastreio} movido para a lista de entregues.')
            self.on_pendentes_activate(button)

    def on_aprastreio_destroy(self, window):
        Gtk.main_quit()
        os.unlink(pidfile)

    def on_btnLimpar_clicked(self, button):
        self.txtRastreio.set_text('')
        self.txtObjeto.set_text('')
        self.txtcampobuffer.set_text('')


builder = Gtk.Builder()
builder.add_from_file('aprastreio.ui')
builder.connect_signals(Rastreio())
janela = builder.get_object('aprastreio')
janela.show_all()
Gtk.main()
