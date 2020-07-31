#!/usr/bin python
# -*- coding: utf-8 -*-
'''
Created on Mar 21, 2018

@author: Wei Wang
'''

from Bio import Entrez
import json, nltk, re, html, os, sys, csv
from datetime import datetime
# from textan import FeatureExtractor

class TextUtility():
    
    @staticmethod
    def find_sub_string_location(text, sub):
        if len(text)==0:
            return (0, 0)
        
        posStart = text.lower().find(sub.lower())
        if posStart < 0:
            return (0, 0)
        else:
            return (posStart, posStart+len(sub))
        
    @staticmethod
    def find_multiple_substring_locations(subs, text):
        if len(text)==0:
            return (0, 0)
        
        text = text.lower()
        pstart = 0
        segs = []
        for sub in subs:
            pos = text[pstart:].find(sub.lower())
            if pos < 0:
                segs.append((0, 0))
                pstart = pstart + len(sub)
            else:
                segs.append((pos + pstart, pos+len(sub)+pstart))
                pstart = pos + len(sub) + pstart
            
        return segs

    @staticmethod
    def find_multiple_token_locations(words, sentence):        
        tokens = nltk.word_tokenize(sentence.lower())
        
        n = len(tokens)
        locsTokenStarts = [-1] * n
        curpt = 0
        for i in range(n):
            pos = sentence[curpt:].find(tokens[i])
            locsTokenStarts[i] = pos + curpt
            curpt = locsTokenStarts[i] + len(tokens[i])
        
        segs = [(locsTokenStarts[i], locsTokenStarts[i]+len(tokens[i])) for i in range(n)]
        return segs
        
    @staticmethod
    def find_token_locations(tokens, sentence):        
        n = len(tokens)
        locsTokenStarts = [-1] * n
        curpt = 0
        for i in range(n):
            pos = sentence[curpt:].find(tokens[i])
            locsTokenStarts[i] = pos + curpt
            curpt = locsTokenStarts[i] + len(tokens[i])
        return locsTokenStarts
    
    ###: This function find the range of sub in the text. Sub is a token set obtained from the full text. 
    @staticmethod
    def find_sub_text_range_minimal_cover(text, sub):
        if len(text)==0:
            return (0, 0)
        
        text = text.lower()
    #    tokens = text.split()
        tks = nltk.word_tokenize(text)
        tokens=[]
        for t in tks:
            tokens+=re.split('-|/', t)
        n = len(tokens)
        #print tokens
        
        ###: find starting locations of all tokens
        charlocs = [-1] * n
        curpt = 0
        for i in range(n):
            pos = text[curpt:].find(tokens[i])
            charlocs[i] = pos + curpt
            curpt = charlocs[i] + len(tokens[i])
            
        s = sub.lower()
#         words0 = re.split(', | ', s)
        words0 = nltk.word_tokenize(s)
        words = list(set(words0)) # remove duplicates
        tags = [-1] * n
        for i, w in enumerate(words):
            indices = [j for (j, t) in enumerate(tokens) if w==t or '('+ w +')'==t]
            for j in indices:
                tags[j] = i
        wtags = [-1] * len(words0)
        for i, w in enumerate(words):
            indices = [j for (j, t) in enumerate(words0) if w==t or '('+ w +')'==t]
            for j in indices:
                wtags[j] = i
        
        m = len(words)
        wcount = [0]*m
        for i in range(m):
            ts = [wt for wt in wtags if wt==i]
            wcount[i] = len(ts)
            
        inz = [i for (i, t) in enumerate(tags) if t >= 0]
        if not inz:  
            return (0, len(text))
        ileft = min(inz)
        iright = max(inz)
    
        tgs = tags[ileft:iright+1]
        spans = range(len(words), len(tgs)+1)    
        for width in spans:
            for i in range(n-width):
                ts = tgs[i:i+width]
                found = True
                for k in range(m):
                    locs = [k for t in ts if k==t]
                    if len(locs) < wcount[k]:
                        found = False
                        break
                    
                if found:
                    start_char = charlocs[ileft+i]
                    end_char = charlocs[ileft+i+width-1]+len(tokens[ileft+i+width-1])
                    return (start_char, end_char)
        
        #return (None, None)
        return (0, len(text))
    
    ###: This function find the range of sub in the text. Sub is a token set obtained from the full text. 
    @staticmethod
    def find_sub_text_range_minimal_cover_multiple(text, subs):
        if len(text)==0:
            return (0, 0)
        
        text = text.lower()
    #    tokens = text.split()
        tks = nltk.word_tokenize(text)
        tokens=[]
        for t in tks:
            tokens+=re.split('-|/', t)
        numtokens = len(tokens)
        #print tokens
        
        ###: find starting locations of all tokens
        charlocs = [-1] * numtokens
        curpt = 0
        for i in range(numtokens):
            pos = text[curpt:].find(tokens[i])
            charlocs[i] = pos + curpt
            curpt = charlocs[i] + len(tokens[i])
        
        pos = 0
        spans = []
        for sub in subs:
            s = sub.lower()
            words0 = nltk.word_tokenize(s)
            words = [w for w in words0 if re.match('\w+', w)]
            
            while words[0]!=tokens[pos] and pos < numtokens-1:
                pos += 1
            startPos = charlocs[pos]
            for word in words[1:]:
                while word!=tokens[pos] and pos < numtokens-1:
                    pos += 1
            endPos = charlocs[pos] + len(words[-1])
            spans.append((sub, startPos, endPos))   
        
        return spans
    
    
    ###: This function find the range of sub in the text. Sub is a token set obtained from the full text. 
    @staticmethod
    def find_sub_text_range(text, sub):
        text = text.lower()
    #    tokens = text.split()
        tks = nltk.word_tokenize(text)
        tokens=[]
        for t in tks:
            tokens+=re.split('-|/', t)
        n = len(tokens)
        #print tokens
        
        ###: find starting locations of all tokens
        charlocs = [-1] * n
        curpt = 0
        for i in range(n):
            pos = text[curpt:].find(tokens[i])
            charlocs[i] = pos + curpt
            curpt = charlocs[i] + len(tokens[i])
            
            
        s = sub.lower()
        words = re.split(', | ', s)
        ranges = []
        leading_word_indices = [i for i, tk in enumerate(tokens) if tk==words[0]]
        if leading_word_indices:
            for leadingIdx in leading_word_indices:
                end = leadingIdx
                toSkip = False
                for w in words[1:]:
                    locs = [i for i, tk in enumerate(tokens[end+1:]) if tk==w]
                    if locs:
                        loc = locs[0]
                        end += loc+1
                    else:
                        toSkip = True
                if not toSkip:      
                    ranges.append((charlocs[leadingIdx], charlocs[end]+len(tokens[end])))
                
        minDist = len(text)
        minRange = (0, len(text))
        for r in ranges:
            if r[1]-r[0] < minDist:
                minRange = r
                minDist = r[1] - r[0]
        
        ##: range is the whole text, this is possiby due to the fact that feature is extracted from the cleaned text,
        ##: e.g., non-ascii characters are removed, as well as certain punctuations such as "'" or "-"
        ##: In this case, the feature word is only required to match the begining part of tokens. 
        if minRange[0]==0 and minRange[1]==len(text):
            minRange = TextUtility.find_sub_text_range_partial_match(text, sub)
        
        return minRange    
    
    ###: This function find the range of sub in the text. Sub is a token set obtained from the full text. 
    @staticmethod
    def find_sub_text_range_partial_match(text, sub):
        text = text.lower()
    #    tokens = text.split()
        tks = nltk.word_tokenize(text)
        tokens=[]
        for t in tks:
            tokens+=re.split('-|/', t)
        n = len(tokens)
        #print tokens
        
        ###: find starting locations of all tokens
        charlocs = [-1] * n
        curpt = 0
        for i in range(n):
            pos = text[curpt:].find(tokens[i])
            charlocs[i] = pos + curpt
            curpt = charlocs[i] + len(tokens[i])
            
            
        s = sub.lower()
        words = re.split(', | ', s)
        ranges = []
        leading_word_indices = [i for i, tk in enumerate(tokens) if tk[:len(words[0])]==words[0]]
        if leading_word_indices:
            for leadingIdx in leading_word_indices:
                end = leadingIdx
                toSkip = False
                for w in words[1:]:
                    locs = [i for i, tk in enumerate(tokens[end+1:]) if tk[:len(w)]==w]
                    if locs:
                        loc = locs[0]
                        end += loc+1
                    else:
                        toSkip = True
                if not toSkip:      
                    ranges.append((charlocs[leadingIdx], charlocs[end]+len(tokens[end])))
                
        minDist = len(text)
        minRange = (0, len(text))
        for r in ranges:
            if r[1]-r[0] < minDist:
                minRange = r
                minDist = r[1] - r[0]
            
        return minRange    
    

    @staticmethod
    def tooltip_to_rich_text(text):
        """Convert plain text to rich text so that tooltip word wrap"""
        
        richtext= "<FONT COLOR=black>" + html.escape(text) + "</FONT>"
        return richtext
    
    @staticmethod
    def text_highlight_html(text, segments):
        if len(segments)==0:
            return text
        
        segments.sort(key=lambda seg:seg[0])
        
        ##: Merge overlapped segments
        segs = [segments[0]]
        for posStart, posEnd in segments[1:]:
            if posStart<segs[-1][1]:
                iend = max(posEnd, segs[-1][1])
                segs[-1] = (segs[-1][0], iend)
            else:
                segs.append((posStart, posEnd))
                
        texthtml = ''
        lastPos = 0
        for startPos, endPos in segs:
            texthtml += html.escape(text[lastPos:startPos]) + '<span style="background-color: #FFFF00">' + html.escape(text[startPos:endPos]) + '</span>'
            lastPos = endPos
        texthtml += html.escape(text[lastPos:])
        
#         texthtml = "<pre>" + texthtml + "</pre>"
        texthtml = texthtml.replace("\n", "<br/>") 
        return texthtml
    
    @staticmethod
    def isfloat(s):
        try:
            float(s)
            return True
        except ValueError:
            return False    

class MedLineAbstract():
    def __init__(self, PMID, abstract, title, journal, pubTypes, meshTerms, chemicals):
        self.PMID = PMID
        self.abstract = abstract 
        self.title = title
        self.journal = journal  
        self.publicationTypes = pubTypes
        self.meshHeadings = meshTerms
        self.chemicals = chemicals
    
    def setAbstract(self, text):
        self.abstract = text
        
    def getAbstract(self):
        return self.abstract
    
    def getMeshTerms(self):
        return self.meshHeadings
    
    def getChemicals(self):
        return self.chemicals
    
    def getData(self):
        data = [self.PMID, self.abstract, self.title, self.journal, self.publicationTypes, self.meshHeadings, self.chemicals]
        return data

class PubMedUtility():
    
    @staticmethod
    def search(query, emailAddress, maxRecords = 20):
        Entrez.email = emailAddress
        handle = Entrez.esearch(db = 'pubmed',
                                sort = 'relevance', #'pub date', # 
                                retmax = str(maxRecords), 
                                retmode = 'text',
                                term = query)
        
        results = Entrez.read(handle)
    #   To get the citation IDs, try results['IdList']
        return results
    
    @staticmethod
    def searchAbstract(query, emailAddress, maxRecords = 20):
        Entrez.email = emailAddress
        handle = Entrez.esearch(db = 'pubmed',
                                sort = 'relevance', #'pub date', # 
                                retmax = str(maxRecords), 
                                retmode = 'text',
                                field = 'title/abstract',
                                term = query)
        
        results = Entrez.read(handle)
    #   To get the citation IDs, try results['IdList']
        return results
    
    @staticmethod
    def fetch_details(id_list, emailAddress):
        ids = ','.join(id_list)
        Entrez.email = emailAddress
        handle = Entrez.efetch(db = 'pubmed',
                               retmode = 'xml',
                               rettype = 'medline',
                               id = ids)
        
        results = Entrez.read(handle)
        return results
    
    @staticmethod
    def fetch_details_text(id_list, emailAddress, filename):
        ids = ','.join(id_list)
        Entrez.email = emailAddress
        handle = Entrez.efetch(db = 'pubmed',
                               retmode = 'xt',
                               rettype = 'medline',
                               id = ids)
        
#         results = Entrez.read(handle)
        results = handle.read()
        
        out_file = open(filename, "w")

        for line in results:
            out_file.write(line)
        
        out_file.close()
        handle.close()
        
#         return results
    
    @staticmethod
    def dumpToFile( object, fileName):
        
        sortKeys = False
        indentSize = 3
        data = json.dumps(object, default = lambda o: o.__dict__, 
                          sort_keys = sortKeys, 
                          indent = indentSize)    
        
        jsonStr = json.loads(data)
        
        with open(fileName, 'w') as output:
            json.dump(jsonStr, output, sort_keys = sortKeys, indent = indentSize)
            
        output.close()
    
    @staticmethod
    def find_gene_articles(gene, maxRecords):
        emailAddress = 'jjttww2@yahoo.com'
        results = PubMedUtility.search('KRAS', emailAddress, maxRecords)
        id_list = results['IdList']
        papers = PubMedUtility.fetch_details(id_list, emailAddress)
        pubmedArticles = papers['PubmedArticle']
        return pubmedArticles
    
def create_gene_list():
    datapath = "./datasources/"
    filename_genes=os.path.abspath('./datasources/list_of_genes.txt')
    list_genes=eval(open(filename_genes).read())
    
    genes_aliases=eval(open('./datasources/genes_aliases_.txt').read())
    aliases = [alias for gn, alias in genes_aliases]
    list_genes += aliases
    list_genes = [gene for gene in list_genes]
    
    try:
        with open(datapath + 'list_of_gene_synonyms.json', 'r') as json_data:
            gene_syns = json.load(json_data)
    except Exception as e:
        print(str(e))
        sys.exit()
    gene_synonyms = [syno for gene, syno in gene_syns]
    list_genes += gene_synonyms
    
    try:
        with open(datapath + 'list_of_gene_names.json', 'r') as json_data:
            gene_names = json.load(json_data)
    except Exception as e:
        print(str(e))
        sys.exit()
    gene_full_names = [name for gene, name in gene_names]
    list_genes += gene_full_names
    
    list_genes = set(list_genes)
    list_genes = [gn for gn in list_genes if len(gn)>1 and not gn.isdigit()] ## Exclude single letters and numbers
    
    return list_genes


def pull_gene_articles():
    gene_list = create_gene_list()
    gene_list.sort()
    gene_list = ['"' + gene +'"' if len(gene.split())>1 else gene for gene in gene_list]
    totalnum = len(gene_list)
    emailAddress = 'jjttww2@yahoo.com'
    maxRecords = 500000    
#     blocksize = 100
    blocksize = 50
    nblk = int(totalnum/blocksize)
    pmid_list = set([])
    s2 = ") AND (((cancer OR tumor OR tumour OR neoplasm OR carcinoma) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant))"
    for i in range(nblk+1):
        if i<4094:
            continue
        
        istart = blocksize*i+1
        iend = blocksize*(i+1)
        iend = min(iend, totalnum)
        genes = gene_list[istart:iend]
        s1 = ' OR '.join(genes)
        query = "(" + s1 + s2
        
        try:
            results = PubMedUtility.search(query, emailAddress, maxRecords) 
        except:
            print(str(iend) + ' missing!')
            continue
#         results = PubMedUtility.search(query, emailAddress, maxRecords)
        pmids = results['IdList']
        for pid in pmids:
            pmid_list.add(pid)
        
        print("gene number = " + str(iend) + "; PMIDs = " + str(len(pmids))+"; All PMIDs = " + str(len(pmid_list)))
    
        try:
            with open("PMIDS4genes.csv", 'w', newline='') as f:
                featurewriter = csv.writer(f, dialect='excel', delimiter=',')
                for r in pmid_list:
                    featurewriter.writerow([r])
        except Exception as e:
            print(str(e))
    
    print("Function finished!")
    
def pull_articles_1gene_per_query():
    ###################################################
    ##: Create gene symbol-alias look-up table.
    ###################################################
    datapath = "./datasources/"
    filename_genes=os.path.abspath('./datasources/list_of_genes.txt')
    list_genes=eval(open(filename_genes).read())
    
    genes_aliases=eval(open('./datasources/genes_aliases_.txt').read())
    
    alias_genes = [(alias, gn) for gn, alias in genes_aliases]
    dictAliases = dict(alias_genes)
    
    aliases = [alias for gn, alias in genes_aliases]
    list_genes += aliases
#     list_genes = [gene for gene in list_genes]
    
    try:
        with open(datapath + 'list_of_gene_synonyms.json', 'r') as json_data:
            gene_syns = json.load(json_data)
    except Exception as e:
        print(str(e))
        sys.exit()
    gene_synonyms = [syno for gene, syno in gene_syns]
    list_genes += gene_synonyms
    
    for gene, syno in gene_syns:
        dictAliases[syno] = gene

##: Not to include gene names
#     try:
#         with open(datapath + 'list_of_gene_names.json', 'r') as json_data:
#             gene_names = json.load(json_data)
#     except Exception as e:
#         print(str(e))
#         sys.exit()
#     gene_full_names = [name for gene, name in gene_names]
#     list_genes += gene_full_names
#      
#     for gene, name in gene_names:
#         dictAliases[name] = gene
##: end include gene names
    
    
    list_genes += dictAliases.values()  ##: Add genes in the dict to the list in case they are not in list_of_genes.txt
    
#     list_genes = [gn.lower() for gn in list_genes]
    list_genes = set(list_genes)
    list_genes = [gn for gn in list_genes if len(gn)>1 and not gn.isdigit() and gn.lower() not in ['or', 'not', 'and']] ## Exclude single letters and numbers
    list_genes = list(list_genes)
    list_genes.sort()
    
#     gene_list = create_gene_list()
#     gene_list.sort()
    totalnum = len(list_genes)
    emailAddress = 'jjttww2@yahoo.com'
    maxRecords = 500000    
    
#     pmid_list = set([])
    s2 = ') AND ((((cancer OR tumor OR tumour OR neoplasm OR carcinoma)) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR "clinical characteristic" OR risk OR clinical OR "clinical trial" OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR "copy number" OR "copy number alteration" OR "genomic alteration" OR "wild type" OR fusion OR mutant))'
    
#     s2 = " AND (((cancer OR tumor OR tumour OR neoplasm OR carcinoma) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant))"
    for i, gene in enumerate(list_genes):
        if i%5000==0:
            all_data = {}
            dictPMIDs = {}
            missed_genes = []
            filename = "./data/abstracts/PMIDS4genes-" + str(i) + "-" + str(i+5000) + ".json"
            
        if i%100==0:
            print(str(i) + " out of " + str(totalnum))
            all_data['CurrentIndex'] = i
            all_data['PMIDs'] = dictPMIDs
            all_data['missed'] = missed_genes
            with open(filename, 'w') as output:
                json.dump(all_data, output)
            output.close()
        
#         if gene in dictAliases:
#             alias = gene
#             gene_symbol = dictAliases[gene]
#         else:
#             gene_symbol = gene
#             alias = ''
        
        if len(gene.split())>1:
            query = '("' + gene +'"' + s2
        else:
            query =  '('+ gene + s2
        
#         query = "((not)) AND ((((cancer OR tumor OR tumour OR neoplasm OR carcinoma)) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant)) "
        try:
            results = PubMedUtility.search(query, emailAddress, maxRecords) 
        except:
            print(str(i) + ": " + gene + ' missing!')
            missed_genes.append(i)
            continue
        
        if 'ErrorList' in results:
            if 'PhraseNotFound' in results['ErrorList']:
                continue
            else:
                print(results['ErrorList'])
                continue
        
        if 'WarningList' in results:
            if 'QuotedPhraseNotFound' in results['WarningList']:
                continue
            else:
                print(results['ErrorList'])
                continue
            
#         results = PubMedUtility.search(query, emailAddress, maxRecords)
        pmids = results['IdList']
        if len(pmids)>=260660:  ##: This is the number without gene. When this number extracted, it means the term is ignored, e.g., not, or
            continue
        
        for pid in pmids:
            if not pid in dictPMIDs:
                dictPMIDs[pid] = [i]
            else:
                dictPMIDs[pid].append(i)
        
    
    print(str(i) + " out of " + str(totalnum))
    all_data['CurrentIndex'] = i
    all_data['PMIDs'] = dictPMIDs
    all_data['missed'] = missed_genes
    with open(filename, 'w') as output:
        json.dump(all_data, output)
    output.close()
            
    print("Function finished!")
    
def pull_articles_1gene_symbol_only_per_query():
    ###################################################
    ##: Create gene symbol-alias look-up table.
    ###################################################
    datapath = "./datasources/"
    filename_genes=os.path.abspath('./datasources/list_of_genes.txt')
    list_genes=eval(open(filename_genes).read())
    
#     list_genes = [gn.lower() for gn in list_genes]
    list_genes = set(list_genes)
    list_genes = [gn for gn in list_genes if len(gn)>1 and not gn.isdigit() and gn.lower() not in ['or', 'not', 'and']] ## Exclude single letters and numbers
    list_genes = list(list_genes)
    list_genes.sort()
    
#     gene_list = create_gene_list()
#     gene_list.sort()
    totalnum = len(list_genes)
    emailAddress = 'jjttww2@yahoo.com'
    maxRecords = 500000    
    
#     pmid_list = set([])
    s2 = ') AND ((((cancer OR tumor OR tumour OR neoplasm OR carcinoma)) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR "clinical characteristic" OR risk OR clinical OR "clinical trial" OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR "copy number" OR "copy number alteration" OR "genomic alteration" OR "wild type" OR fusion OR mutant))'
    
#     s2 = " AND (((cancer OR tumor OR tumour OR neoplasm OR carcinoma) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant))"
    for i, gene in enumerate(list_genes):
#         if i<3518:
#             continue
        
        if i%5000==0:
            all_data = {}
            dictPMIDs = {}
            missed_genes = []
            filename = "./data/abstracts2/PMIDS4genes-" + str(i) + "-" + str(i+5000) + ".json"
            
        if i%100==0:
            print(str(i) + " out of " + str(totalnum))
            all_data['CurrentIndex'] = i
            all_data['PMIDs'] = dictPMIDs
            all_data['missed'] = missed_genes
            with open(filename, 'w') as output:
                json.dump(all_data, output)
            output.close()
        
#         if gene in dictAliases:
#             alias = gene
#             gene_symbol = dictAliases[gene]
#         else:
#             gene_symbol = gene
#             alias = ''
        
        if len(gene.split())>1:
            query = '("' + gene +'"' + s2
        else:
            query =  '('+ gene + s2
        
#         query = "((not)) AND ((((cancer OR tumor OR tumour OR neoplasm OR carcinoma)) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant)) "
        try:
#             results = PubMedUtility.search(query, emailAddress, maxRecords) 
            results = PubMedUtility.searchAbstract(query, emailAddress, maxRecords) 
        except:
            print(str(i) + ": " + gene + ' missing!')
            missed_genes.append(i)
            continue
        
        if 'ErrorList' in results:
            if 'PhraseNotFound' in results['ErrorList']:
                continue
            else:
                print(results['ErrorList'])
                continue
        
        if 'WarningList' in results:
            if 'QuotedPhraseNotFound' in results['WarningList']:
                continue
            else:
                print(results['ErrorList'])
                continue
            
#         results = PubMedUtility.search(query, emailAddress, maxRecords)
        pmids = results['IdList']
        if len(pmids)>=260660:  ##: This is the number without gene. When this number extracted, it means the term is ignored, e.g., not, or
            continue
        
        for pid in pmids:
            if not pid in dictPMIDs:
                dictPMIDs[pid] = [i]
            else:
                dictPMIDs[pid].append(i)
        
    
    print(str(i) + " out of " + str(totalnum))
    all_data['CurrentIndex'] = i
    all_data['PMIDs'] = dictPMIDs
    all_data['missed'] = missed_genes
    with open(filename, 'w') as output:
        json.dump(all_data, output)
    output.close()
            
    print("Function finished!")
    
def combine_gene_articles_PMIDs():
    
    filename1 = 'PMIDS4genes.p1.csv'
    try:
        with open(filename1, 'r') as csvfile:
            reader = csv.reader(csvfile)
#             truth = [row for row in reader if row[1] in id_list]
            PMIDs = [row[0] for row in reader]
    except Exception as e:
        print(str(e))
    
    filename2 = 'PMIDS4genes.csv'
    try:
        with open(filename2, 'r') as csvfile2:
            reader = csv.reader(csvfile2)
#             truth = [row for row in reader if row[1] in id_list]
            PMIDs2 = [row[0] for row in reader]
    except Exception as e:
        print(str(e))
    
    allPMIDs = list(set(PMIDs).union(set(PMIDs2)))
    allPMIDs.sort()
    
    try:
        with open("PMIDS4genesAll.csv", 'w', newline='') as f:
            featurewriter = csv.writer(f, dialect='excel', delimiter=',')
            for r in allPMIDs:
                featurewriter.writerow([r])
    except Exception as e:
        print(str(e))
    
def pull_gene_articles_abstracts_v1():
    filename = 'PMIDS4genesAll.csv'
    try:
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
#             truth = [row for row in reader if row[1] in id_list]
            PMIDs = [row[0] for row in reader]
    except Exception as e:
        print(str(e))
        
    emailAddress = 'jjttww2@yahoo.com'
    totalnum = len(PMIDs)
    blocksize = 500000000
    blocksize = 10000
    nblk = int(totalnum/blocksize)
    for i in range(nblk+1):
        istart = blocksize*i
        iend = blocksize*(i+1)
        iend = min(iend, totalnum)
        
        pmid_list = PMIDs[istart:iend]
        pmid_start = pmid_list[0]
        pmid_end = pmid_list[-1]
        
        fname = "./data/abstracts/abstracts-10062018-" + pmid_start + '-' +pmid_end+'.txt'
#         fname = "./data/abstracts-10062018-all.txt"
        
        print( str(i)+" out of " + str(nblk+1)+ ': Fetching ' + pmid_start + '-' + pmid_end +'...')
        PubMedUtility.fetch_details_text(pmid_list, emailAddress, fname)
    
    print("Function finished!")
        
def pull_gene_articles_abstracts(fdir):
#     fdir = './data/abstracts'
    
    filenames = os.listdir(fdir)
    reportnames = [fn for fn in filenames if fn.startswith('PMIDS4') and fn.endswith('json')]
#         reportnames = [str(fn.replace('\\','/')) for fn in reportnames]
    reportnames = [str(fn) for fn in reportnames]
    
#     for fname in reportnames:
#         pos1 = fname.find('-')
#         pos2 = fname.rfind('-')
#         num = int(fname[pos1+1:pos2])
#         n1 = int(num/5000)
#         n2 = n1+5000
#         
#         s = str(n1)+'-'+str(n2)
#         filename = fname[:pos1+1] + s + '.json'
#         
#         os.rename(fdir + '/'+fname, fdir + '/'+filename)
    
    all_data = {}
    all_dictPMIDs = {}
    all_missed_genes = []
    
#     reportnames = reportnames[:19] + reportnames[20:]
    for n, filename in enumerate(reportnames):
        try:
            with open(fdir + '/' + filename, 'r') as json_data:
                data = json.load(json_data)
                print("Loaded #" + str(n) + ": " + filename)
        except Exception as e:
            print(str(e))
            sys.exit()
        
        dictPMIDs = data['PMIDs']
        missed_genes = data['missed']
        
        for i, pid in enumerate(dictPMIDs):
            if i%10000==0:
                print(str(i)+' out of '+str(len(dictPMIDs))+" into " + str(len(all_dictPMIDs)))
                
            if pid in all_dictPMIDs:
                all_dictPMIDs[pid] += dictPMIDs[pid]
            else:
                all_dictPMIDs[pid] = dictPMIDs[pid]
            
            pds = list(set(all_dictPMIDs[pid]))
            pds.sort()
            all_dictPMIDs[pid] = pds
        
        all_missed_genes += missed_genes
    
#     for pid in all_dictPMIDs:
#         pds = list(set(all_dictPMIDs[pid]))
#         pds.sort()
#         all_dictPMIDs[pid] = pds
    
    all_data['PMIDs'] = all_dictPMIDs
    all_data['missed'] = all_missed_genes
    print('dumping all data...')
    with open(fdir+"/abstracts-all-12-02-2018.json", 'w') as output:
        json.dump(all_data, output)
    output.close()
    print('dumping all data... done!')
            
#     filename = 'PMIDS4genesAll.csv'
#     try:
#         with open(filename, 'r') as csvfile:
#             reader = csv.reader(csvfile)
# #             truth = [row for row in reader if row[1] in id_list]
#             PMIDs = [row[0] for row in reader]
#     except Exception as e:
#         print(str(e))
    
    PMIDs = list(all_dictPMIDs.keys())
    PMIDs.sort()
    emailAddress = 'jjttww2@yahoo.com'
    totalnum = len(PMIDs)
#     blocksize = 500000000
    blocksize = 10000
    nblk = int(totalnum/blocksize)
    for i in range(nblk+1):
        istart = blocksize*i
        iend = blocksize*(i+1)
        iend = min(iend, totalnum)
        
        pmid_list = PMIDs[istart:iend]
        pmid_start = pmid_list[0]
        pmid_end = pmid_list[-1]
        
        fname = "./data/abstracts2/abstracts-12-02-2018-" + pmid_start + '-' +pmid_end+'.txt'
#         fname = "./data/abstracts-10062018-all.txt"
        
        print( str(i)+" out of " + str(nblk+1)+ ': Fetching ' + pmid_start + '-' + pmid_end +'...')
        PubMedUtility.fetch_details_text(pmid_list, emailAddress, fname)
    
    
    print("Function finished!")
    
# 
# def pull_gene_articles_abstracts_symbol_only():
#     
#     fdir = './data/abstracts2'
#     filenames = os.listdir(fdir)
#     reportnames = [fn for fn in filenames if fn.startswith('PMIDS4') and fn.endswith('json')]
# #         reportnames = [str(fn.replace('\\','/')) for fn in reportnames]
#     reportnames = [str(fn) for fn in reportnames]
#     
# #     for fname in reportnames:
# #         pos1 = fname.find('-')
# #         pos2 = fname.rfind('-')
# #         num = int(fname[pos1+1:pos2])
# #         n1 = int(num/5000)
# #         n2 = n1+5000
# #         
# #         s = str(n1)+'-'+str(n2)
# #         filename = fname[:pos1+1] + s + '.json'
# #         
# #         os.rename(fdir + '/'+fname, fdir + '/'+filename)
#     
#     all_data = {}
#     all_dictPMIDs = {}
#     all_missed_genes = []
#     
# #     reportnames = reportnames[:19] + reportnames[20:]
#     for n, filename in enumerate(reportnames):
#         try:
#             with open(fdir + '/' + filename, 'r') as json_data:
#                 data = json.load(json_data)
#                 print("Loaded #" + str(n) + ": " + filename)
#         except Exception as e:
#             print(str(e))
#             sys.exit()
#         
#         dictPMIDs = data['PMIDs']
#         missed_genes = data['missed']
#         
#         for i, pid in enumerate(dictPMIDs):
#             if i%10000==0:
#                 print(str(i)+' out of '+str(len(dictPMIDs))+" into " + str(len(all_dictPMIDs)))
#                 
#             if pid in all_dictPMIDs:
#                 all_dictPMIDs[pid] += dictPMIDs[pid]
#             else:
#                 all_dictPMIDs[pid] = dictPMIDs[pid]
#             
#             pds = list(set(all_dictPMIDs[pid]))
#             pds.sort()
#             all_dictPMIDs[pid] = pds
#         
#         all_missed_genes += missed_genes
#     
# #     for pid in all_dictPMIDs:
# #         pds = list(set(all_dictPMIDs[pid]))
# #         pds.sort()
# #         all_dictPMIDs[pid] = pds
#     
#     all_data['PMIDs'] = all_dictPMIDs
#     all_data['missed'] = all_missed_genes
#     print('dumping all data...')
#     with open(fdir+"/abstracts-all-10-22-2018.json", 'w') as output:
#         json.dump(all_data, output)
#     output.close()
#     print('dumping all data... done!')
#             
# #     filename = 'PMIDS4genesAll.csv'
# #     try:
# #         with open(filename, 'r') as csvfile:
# #             reader = csv.reader(csvfile)
# # #             truth = [row for row in reader if row[1] in id_list]
# #             PMIDs = [row[0] for row in reader]
# #     except Exception as e:
# #         print(str(e))
#     
#     PMIDs = list(all_dictPMIDs.keys())
#     PMIDs.sort()
#     emailAddress = 'jjttww2@yahoo.com'
#     totalnum = len(PMIDs)
# #     blocksize = 500000000
#     blocksize = 10000
#     nblk = int(totalnum/blocksize)
#     for i in range(nblk+1):
#         istart = blocksize*i
#         iend = blocksize*(i+1)
#         iend = min(iend, totalnum)
#         
#         pmid_list = PMIDs[istart:iend]
#         pmid_start = pmid_list[0]
#         pmid_end = pmid_list[-1]
#         
#         fname = fdir + "/abstracts-10-19-2018-" + pmid_start + '-' +pmid_end+'.txt'
# #         fname = "./data/abstracts-10062018-all.txt"
#         
#         print( str(i)+" out of " + str(nblk+1)+ ': Fetching ' + pmid_start + '-' + pmid_end +'...')
#         PubMedUtility.fetch_details_text(pmid_list, emailAddress, fname)
#     
#     
#     print("Function finished!")
    
def test():
    gene = '"fecal transplant"'
    gene = 'not'
    emailAddress = 'jjttww2@yahoo.com'
    maxRecords = 500000    
    
#     pmid_list = set([])
    s2 = " AND (((cancer OR tumor OR tumour OR neoplasm OR carcinoma) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant))"

    if len(gene.split())>1:
        query = '"' + gene +'"' + s2
    else:
        query = gene + s2
    
#     query = gene
#     query = "((AKT1 OR CWS6 OR PKB OR pkb-alpha OR prkca OR RAC OR rac-alpha)) AND ((((cancer OR tumor OR tumour OR neoplasm OR carcinoma)) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant))"
#     query = "((CWS6)) AND ((((cancer OR tumor OR tumour OR neoplasm OR carcinoma)) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant))"
    
    query = "((not)) AND ((((cancer OR tumor OR tumour OR neoplasm OR carcinoma)) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant)) "
    
#     query = '(("breast cancer resistance marker 1")) AND ((((cancer OR tumor OR tumour OR neoplasm OR carcinoma)) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant)) '
    
    query = '(("tumor Necrosis factor binding protein 2")) AND ((((cancer OR tumor OR tumour OR neoplasm OR carcinoma)) AND (prognosis OR predictive OR survival OR outcome OR response OR sensitivity OR resistance OR clinical characteristic OR risk OR clinical OR clinical trial OR treatment OR therapy)) AND (mutation OR mutations OR amplification OR deletion OR rearrangement OR copy number OR copy number alteration OR genomic alteration OR wild type OR fusion OR mutant)) '
    try:
        results = PubMedUtility.search(query, emailAddress, maxRecords) 
    except:
        print( gene + ' missing!')
    
    pmids = results['IdList']
    print(pmids)
    
def load_medline_datafile_abstracts(filename):
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            lines = [line.rstrip() for line in lines] 
    except Exception as e:
        print(str(e))
    
    idlines = []
    for i, line in enumerate(lines):
        if line.startswith('PMID-'):
            idlines.append(i)
    idlines.append(len(lines))

    
    medlineAbstracts = []
    medlineTexts = []
    num = len(idlines)-1
    for i in range(num):
        print('Analyzing article ' + str(i))
        textlines = lines[idlines[i]:idlines[i+1]]
        sections = {'PMID-':[], 'AB  -':[], 'TI  -':[], 'JT  -':[], 'MH  -':[], 'RN  -':[], 'PT  -':[]}
        in_section = False
        for line in textlines:
            s5 = line[:5]
            if s5.strip()!='':
                in_section = False
            
            if s5 in sections:
                sect = sections[s5]
                sect.append(line[5:].strip())
                in_section = True
                
            if s5.strip()=='' and in_section:
                sect.append(line.strip())
    
        PMID = sections['PMID-'][0]        
        abstract = ' '.join(sections['AB  -'])
        title = ' '.join(sections['TI  -'])
        journal = ' '.join(sections['JT  -'])
        meshTerms = '; '.join(sections['MH  -'])
        chemicals = '; '.join(sections['RN  -'])
        pubTypes = '; '.join(sections['PT  -'])
        medAb = MedLineAbstract(PMID, abstract, title, journal, pubTypes, meshTerms, chemicals)
#         article = None
        medlineAbstracts.append(medAb)
        medlineTexts.append('\n'.join(textlines))
    
    return medlineAbstracts , medlineTexts
    
# def generate_pubmed_DB_tables(datafile):

#     pubmed_record_details_header= ["pmid", "title", "abstract", "full_medline", "retrieval_time"]
#     pubmed_publication_types_header= ["pmid", "publication_type"]
#     ether_pubmed_abstract_features_header = ["pmid", "feature_id", "feature_type", "feature_text", "sentence_number", 
#                                              "start_position", "end_position", "preferred_term", "clean_text"]
        
#     outfile1 = "./data/pubmed_record_details.csv"
#     out_file1 = open(outfile1, "w", newline='')    
#     csvwriter_record_detail = csv.writer(out_file1, dialect='excel', delimiter=',')
#     csvwriter_record_detail.writerow(pubmed_record_details_header)
    
#     outfile2 = "./data/pubmed_publication_types.csv"
#     out_file2 = open(outfile2, "w", newline='')    
#     csvwriter_type = csv.writer(out_file2, dialect='excel', delimiter=',')
#     csvwriter_type.writerow(pubmed_publication_types_header)

#     outfile3 = "./data/ether_pubmed_abstract_features.csv"
                                                                                                                                                                                                                                                                                          
#     out_file3 = open(outfile3, "w", newline='')    
#     csvwriter_ether = csv.writer(out_file3, dialect='excel', delimiter=',')
#     csvwriter_ether.writerow(ether_pubmed_abstract_features_header)
    
#     medlineArticles, medlineTexts = load_medline_datafile_abstracts(datafile)
        
        
#     fe = FeatureExtractor()
#     for i, article in enumerate(medlineArticles):
#         print(i)
#         fulltext = medlineTexts[i]        
#         data = article.getData()
#         [pmid, abstract, title, journal, pubTypes, meshTerms, chemicals] = data
        
        
#         csvwriter_record_detail.writerow([pmid, title, abstract, fulltext, datetime.today().isoformat().split('T')[0]])
#         csvwriter_type.writerow([pmid, pubTypes])
        
        
#         features = fe.extract_features_pubmed_abstract(abstract, ['SYMPTOM',"DIAGNOSIS","DRUG"])
#         for j, (ftyp, startPos, endPos, ftext, sentNum, pt, ptclean) in enumerate(features):
# #             print(pid, ftyp, startPos, endPos, ftext)
#             csvwriter_ether.writerow([pmid, str(j), ftyp, ftext, sentNum, startPos, endPos, pt, ptclean])

        
            
#     out_file1.close()
#     out_file2.close()
#     out_file3.close()
        
#     print("Function finished!")
            
if __name__ == '__main__':
    pass
#     test()    
    # generate_pubmed_DB_tables("./data/abstracts-10-19-2018-30266252-7734145.txt")
#     pull_articles_1gene_symbol_only_per_query()
#     pull_articles_1gene_per_query()

#     pull_gene_articles_abstracts("./data/abstracts2")
#     pull_gene_articles_abstracts()
    
#     emailAddress = 'jjttww2@yahoo.com'
#     maxRecords = 20    
#     results = PubMedUtility.search('KRAS', emailAddress, maxRecords)
#     id_list = results['IdList']
# #     id_list = ['24928083', '24903964']
#     id_list = ['24968756', '24960403', '24928083', '24915778', '24903964', '24888607', '24887488', '24885982', '24867540', '24857345', 
#                '24852116', '24846037', '24832158', '24816724', '24800948']
#  
# #     papers = PubMedUtility.fetch_details(id_list, emailAddress)
#     papers = PubMedUtility.fetch_details_text(id_list, emailAddress)
#     pubmedArticles = papers['PubmedArticle']
#     pubmedBooks = papers['PubmedBookArticle']
#     pubmedRecords = []
#     medlineCiations = []
#     PubMedUtility.dumpToFile(pubmedArticles, "KRAS.json")
#     for i, paper in enumerate(pubmedArticles):
#         medlineCitation = paper['MedlineCitation']
#         pubmedData = paper['PubmedData']
#         print("%d) %s" % (i+1, paper['MedlineCitation']['Article']['ArticleTitle']))
