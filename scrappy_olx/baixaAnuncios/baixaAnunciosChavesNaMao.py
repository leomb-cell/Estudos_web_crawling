#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: jeovanio


Simples Web Crawling com Selenium para baixar anuncios selecionados do OLX


requeriments:
instalar geckodriver para o navegador que se quer usar, p.e.:
sudo apt install firefox-geckodriver

instalar o selenium:
pip install selenium

pip install psycopg2-binary


"""


from selenium import webdriver

from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
#from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
#from selenium.webdriver.common.keys import Keys

import psycopg2

import logging
import time

import sys
import pandas as pd


##########################################################
# Le a pagina atual, carrega os elementos desejados, verifica se tem mais páginas e avança antes de retornar
# Se não tiver mais página, retorna 0, senao retorna numero proxima pagina

def LePagina(driver, url_pagina_inicial, page):
    
    #driver.get(url_pagina_inicial+'?o='+str(page))




    content = driver.find_element(By.TAG_NAME,"article")
    
    
    listaContainer = content.find_element(By.ID,"listing")
    
    #lstAds = listaContainer.find_elements(By.CLASS_NAME,'card-module__1awNxG__cardContent')
    lstAds = listaContainer.find_elements(By.CLASS_NAME,"styles-module__saqrOW__card")  
              
    if len(lstAds)>0:
       bAchou = True
       print("Achei ",len(lstAds),"anúncios na página")
    else:
       print("Não Achei anuncios")
       bAchou = False
    
    
    
    lstRetorno = []

    cont = 0
    
    #imprime resultados parciais
    for i in range(len(lstAds)): 
        tag = lstAds[i]
        valores = tag.find_element(By.TAG_NAME,"p")
        
        preco_txt = valores.text.split("\n")[0][3:].replace(".","")
        cond_txt = valores.text.split("\n")[1][9:].replace(".","")
        try:
            preco = float(preco_txt)
            cond = float(cond_txt)
        except:
            preco = 0
            cond = 0
        atributos = tag.find_element(By.CLASS_NAME,"style-module__PkTDxW__list")
        quartos = 0
        area = 0
        vagas = 0
        bwc = 0
        lstAtribs = atributos.text.split("\n")
        for a in lstAtribs:
            if "m²" in a:
                area = float(a[:-2])
            elif " Quartos" in a:
                quartos = int(a[:-8])
            elif " Garagem" in a:
                vagas = int(a[:-8])
            elif " Banheiros" in a:
                bwc = int(a[:-10])
                
        
        #Mobiliado ou nao
        descricao = tag.find_element(By.CLASS_NAME,"style-module__PkTDxW__content")
        mobiliado = False
        if "mobilia" in descricao.text.lower():
            mobiliado = True
        
        
        #Pega o Id desse anuncio
        anchor = tag.find_element(By.TAG_NAME,"a")
        href = anchor.get_attribute("href")
        id_ref = href.split("/id-")[1][:-1]
        
        
        #Monta entrada como um dicionario de retorno
        ad_dict = {
                    "id_ref": id_ref,
                    "descricao": descricao.text,
                    "href": href,
                    "preco": preco,
                    "cond": cond,
                    "quartos": quartos,
                    "area": area,
                    "vagas": vagas,
                    "bwc": bwc,
                    "mobiliado": mobiliado
                  }        
        
        lstRetorno.append(ad_dict)
        cont += 1
        print("Anuncio", cont, "capturado..")
        
        
    



    #verifica se tem outra página
    
    #ls = content.find_elements_by_tag_name('a')
    #achei = False
    #for c in ls:
    #    if (c.get_attribute('data-lurker-detail')=='next_page'):
    #        elem = c
    #        achei = True
    #        break   
    #if (achei):
    #    print("Tem mais página")        
    #    page += 1
    #    return page,lstRetorno
    #else:
    
    return 0,lstRetorno
##############################################################################
def CarregaDadosCNM(logger, maxPages=1):
    

    
    logger.info("Abrindo sessao webdriver")
    driver = webdriver.Firefox()
    driver.implicitly_wait(2) # seconds
    logger.info("Abrindo pagina inicial")
    lstAnuncios = []
    
    try:
        
        page = 1
        #pagina_inicial = "https://www.chavesnamao.com.br/apartamentos-para-alugar/sc-florianopolis/itacorubi/4-quartos/?filtro=ban:2,gar:1"
        pagina_inicial = "https://www.chavesnamao.com.br/apartamentos-a-venda/sc-florianopolis/itacorubi/3-quartos/?filtro=ban:2,gar:1"

        driver.get(pagina_inicial)

        
        print("\n verificar se já conseguiu abrir a página:")
        
        x = input("Terminou de Carregar (S/N):")
        
        
        
        try:
            cookie = driver.find_element(By.CLASS_NAME,"style-module__8KvrsG__Consent")
        
            if (cookie):
                print("Fechando a DIV de consentimentos de cookies")
                #cookie.click()    # aceita os cookies da página
        except:
            print("Nao encontrou a div de aceitaçao de cookie. seguindo assim mesmo...")
        
        #Estabelecida a sessão corretamente
        
        #Lê cada pagina agora
        
        print ("inicio da execução")
        
        page,lstRetorno = LePagina(driver, pagina_inicial, 1)
        lstAnuncios.extend(lstRetorno)   
        
        while (page>0):
            
            #so para controle inicial
            if(page > maxPages): break
        
            print("Pagina:",page)    
        
        
            page,lstRetorno = LePagina(driver, pagina_inicial, page)
            lstAnuncios.extend(lstRetorno)   
            
            #repete o ciclo
            
        print("Fim da captura")
        x = input("Finalizar navegacao? ")
    except:
        print("*****  ERRO  execução captura web com RPA Selenium ****")
        logger.error("*****  ERRO  execução captura web com RPA Selenium ****")
        
        
    #descomentar as linhas abaixo depois da debugagem
    #finally:
        #driver.quit()



    return lstAnuncios



##############################################################################


#main

print("Baixando ańuncios imóveis do site Chaves na Mao")

logger = logging.getLogger('JeoLab_crawl_Sel')

lstAnuncios = CarregaDadosCNM(logger, 100)



#insere cada registro encontrado no anuncio no BD
logger.info("Inserindo registros lidos no BD JeoLAB")
if len(lstAnuncios) > 0:
    colunas = list(lstAnuncios[0].keys())
    registros = []
    for reg in lstAnuncios:
        registros.append(list(reg.values()))
        
        
    #cria um dataframe pandas
    df = pd.DataFrame(registros,columns=colunas)
    
    
    df["preco_por_m2"] = df.preco / df.area


    


