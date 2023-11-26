# -*- coding: utf-8 -*-

import os
import time
from tqdm import tqdm

from multiprocessing import cpu_count
from joblib import Parallel, delayed

from text_to_graph import (TextParser, ToCoocurrence, _rc_dict, encode_pos)
from common_func import save_obj, load_obj, print_time, total_size

from features import FeatureExtractor
# ============================== To transform texts dict ==========
# ===== Text to graph and features

def text_to_text_parsed(text, remove_punct=[]):
    parser = TextParser(remove_punct=remove_punct)
    parsed = parser.define_tagged(text)
    return parsed


def text_parsed_to_graph_sparse_raw(parsed, reduce_classes, graph_type):
    coocurrence = ToCoocurrence(reduce_classes, graph_type)
    coocurrence.grown_graph(parsed)
    sparse, node_names = coocurrence.to_sparse_raw()
    return (sparse, node_names)


def graph_sparse_raw_to_pos_encoded(sparse_raw):
    node_names = sparse_raw[1]
    node_pos = [node[1] for node in node_names]
    node_attr = encode_pos(node_pos)
    return node_attr

def text_parsed_to_features(parsed):
    extractor = FeatureExtractor(parsed=True)
    vec_features = extractor.extract_features(parsed)
    return vec_features

# ========== dict to dict transformations

def dict_to_dict(origin_dict, function, cpu_c,
                 dest_folder, dest_file, log, function_args,
                 use_joblib=None, count_flag=False):
    """Parallel dict to dict process"""

    print('Cores: ', cpu_c, file=log)
    print('Processing to ' + dest_file + '...')
    start_time_p = time.time()
    list_dict = tqdm(list(origin_dict.items()))
    result = \
        Parallel(n_jobs=cpu_c)(
            delayed(lambda x: (x[0], function(x[1], **function_args)))(item)
            for item in list_dict)
    del origin_dict

    # solo util en caso de querer contar cuantas palabras se encontraron
    # en el modelo de lenguaje
    if count_flag:
        exist_counts = [item[1][1] for item in result]
        lens = [item[1][2] for item in result]
        print('exist_counts:', sum(exist_counts), file=log)
        print('lens:', sum(lens), file=log)
        result = [(item[0], item[1][0]) for item in result]

    result = dict(result)
    print_time(start_time_p, 'Process ' + dest_file, log)

    print('Saving with joblib...')
    print('object size: ', total_size(result))
    print('object size: ', total_size(result), file=log)
    start_time_s = time.time()
    save_obj(result, os.path.join(dest_folder, dest_file).replace("\\","/"),
             use_joblib=use_joblib)
    print_time(start_time_s, 'Save ' + dest_file, log)

    print('function_args:', file=log)
    print(function_args, file=log)
    return result

def pipeline_partition_dict(file_dir, text_dict_name, dest_folder, symbol,
                            element_num):
    lst_arch = read_parts(text_dict_name, dest_folder, symbol)
    if lst_arch:
        print('El folder de destino ya tiene archivos, verifica quieras '
              'sobreescribir')
    else:
        text_dict = load_obj(os.path.join(file_dir, text_dict_name).replace("\\","/"), fast=True)
        new_files_prefix = text_dict_name + symbol
        part_pkl(dest_folder, new_files_prefix, text_dict, element_num)
        lst_arch = read_parts(text_dict_name, dest_folder, symbol)
        print('Se crearon total de ', len(lst_arch), ' partes')
        print(lst_arch)    

def pipeline_dict_parsed_and_graphs(origin_dict, dest_label, sufix,
                                    dest_folder, log, cpu_c):
    print('Processing to parsed dict...')
    dest_file = 'parsed_dict' + sufix
    function_args = dict()
    parsed_dict = \
        dict_to_dict(origin_dict, text_to_text_parsed, cpu_c,
                     dest_folder, dest_file, log, function_args)

    # Convert to different graph formats
    gv_op = ['med', 'short', 'full']
    for graph_version in gv_op:
        # Load parsed_dict si no está en memoria
        if 'parsed_dict' not in locals():
            parsed_dict = \
                load_obj(os.path.join(dest_folder, 'parsed_dict' + sufix).replace("\\","/"),
                         fast=True)

        print(f'===== Processing {graph_version} ... =====')
        print('Processing to sparse_raw dict...')
        dest_file = 'sparse_raw_dict_' + graph_version + sufix
        function_args = {'reduce_classes': _rc_dict[graph_version],
                         'graph_type': 'DiGraph'}
        sparse_raw = \
            dict_to_dict(parsed_dict, text_parsed_to_graph_sparse_raw, cpu_c,
                         dest_folder, dest_file, log, function_args)

        print('Processing to pos_encoded dict...')
        dest_file = dest_label + '_' + graph_version + sufix
        function_args = dict()
        pos_encoded = \
            dict_to_dict(sparse_raw, graph_sparse_raw_to_pos_encoded, cpu_c,
                         dest_folder, dest_file, log, function_args)
        del sparse_raw
        del pos_encoded


# ========== Functions to apply transforms to pipeline

def pipeline_dict_main():
    """Function to process texts_dict in parts to default graphs"""
    dataset_name = '22-train'
    element_num = 600

    folder_label = str(None) + '_' + str(element_num)
    symbol = '_%%'
    cpu_c = max([int(cpu_count()*0.5), 1])

    dest_folder = os.path.join('C:/Users/1/Desktop/karina_diploma/AuthorshipVerification-GraphBasedSiameseNetwork/data/PAN22_graphs/',
                               dataset_name + '_' + folder_label).replace("\\","/")
    if not os.path.exists(dest_folder):
        print('... creando folder ', dest_folder)
        os.makedirs(dest_folder)
        

    print('==================================================')
    print('========== Particionando texts_dict')
    file_dir = 'C:/Users/1/Desktop/karina_diploma/AuthorshipVerification-GraphBasedSiameseNetwork/data/PAN22_text_split/' + dataset_name
    text_dict_name = 'texts_dict_clean'
    pipeline_partition_dict(file_dir, text_dict_name, dest_folder, symbol,
                            element_num)

    print('==================================================')
    print('========== Procesando parsed and graphs')
    origin_label = 'texts_dict_clean'
    dest_label = 'pos_encoded_dict'
    log = open(os.path.join(dest_folder, 'log_graphs.txt').replace("\\","/"), 'w+', encoding='utf-8')
    args = [cpu_c]
    apply_to_lst_arch(origin_label, dest_label, dest_folder, symbol, log,
                      pipeline_dict_parsed_and_graphs, args)
    log.close()
    

# ========== Functions to apply transforms to pipeline    

def apply_to_lst_arch(origin_label, dest_label, dest_folder, symbol, log,
                      pipeline_func, pipeline_func_args):
    lst_arch = read_parts(dest_label, dest_folder, symbol)
    if lst_arch:
        print('El folder de destino ya tiene archivos, verifica quieras '
              'sobreescribir')
    else:
        lst_arch = read_parts(origin_label, dest_folder, symbol)
        print('Número de partes: ', len(lst_arch))
        print(lst_arch)
        print('Número de partes: ', len(lst_arch), file=log)
        print(lst_arch, file=log)
        for arch in lst_arch:
            print('\n========== Work in part ' + arch)
            print('\n========== Work in part ' + arch, file=log)
            # Quitamos la extensión
            arch_s, _ = os.path.splitext(arch)
            # Obtenemos sufijo
            sufix = arch_s[arch_s.find(symbol):]
            origin_dict = load_obj(dest_folder + '/' + arch, fast=True)
            pipeline_func(origin_dict, dest_label, sufix, dest_folder, log,
                          *pipeline_func_args)

# ======================================== Files auxiliar transforms
def pipeline_dict_separate_sparse_raw(origin_dict, dest_label, sufix,
                                      dest_folder, log):
    print('Processing to separate...')

    sparse_dict = {k: v[0] for (k, v) in origin_dict.items()}
    nodes_dict = {k: v[1] for (k, v) in origin_dict.items()}
    del origin_dict

    print('To sparse_dict...')
    dest_file = 'sparse_dict_' + dest_label + sufix
    print('Saving with joblib...')
    print('object size: ', total_size(sparse_dict))
    print('object size: ', total_size(sparse_dict), file=log)
    start_time_s = time.time()
    save_obj(sparse_dict, os.path.join(dest_folder, dest_file).replace("\\","/"))
    print_time(start_time_s, 'Save ' + dest_file, log)
    del sparse_dict

    print('To nodes_dict...')
    dest_file = 'nodes_dict_' + dest_label + sufix
    print('Saving with joblib...')
    print('object size: ', total_size(nodes_dict))
    print('object size: ', total_size(nodes_dict), file=log)
    start_time_s = time.time()
    save_obj(nodes_dict, os.path.join(dest_folder, dest_file).replace("\\","/"))
    print_time(start_time_s, 'Save ' + dest_file, log)
    del nodes_dict
    
def separate_sparse_raw():
    # ========== Definir dataset, numero de particiones, compresión
    dataset_name = '22-train'
    element_num = 600

    folder_label = str(None) + '_' + str(element_num)
    symbol = '_%%'

    dest_folder = os.path.join('C:/Users/1/Desktop/karina_diploma/AuthorshipVerification-GraphBasedSiameseNetwork/data/PAN22_graphs/',
                               dataset_name + '_' + folder_label).replace("\\","/")
    if not os.path.exists(dest_folder):
        print('... creando folder ', dest_folder)
        os.makedirs(dest_folder)

    print('==================================================')
    print('========== Separando sparse_raw')

    gv_op = ['med', 'short', 'full']
#     gv_op = ['short']
    for graph_version in gv_op:
        print(f'===== Processing {graph_version} ... =====')
        origin_label = 'sparse_raw_dict_' + graph_version
        dest_label = graph_version
        log = open(os.path.join(dest_folder, 'log_separate.txt').replace("\\","/"), 'w+', encoding='utf-8')
        args = ()
        apply_to_lst_arch(origin_label, dest_label, dest_folder, symbol, log,
                          pipeline_dict_separate_sparse_raw, args)
        log.close()

    print('==================================================')
    print('========== Procesando features')
    log = open(os.path.join(dest_folder, 'log_features.txt').replace("\\","/"), 'w+', encoding='utf-8')
    lst_arch = read_parts('parsed_dict', dest_folder, symbol)
    print('Número de partes: ', len(lst_arch))
    print(lst_arch)
    print('Número de partes: ', len(lst_arch), file=log)
    print(lst_arch, file=log)
    

    # ===== Split dict in parts
    cpu_c = max([int(cpu_count()*0.25), 1])
    use_joblib = None

    for arch in lst_arch:
        print('\n========== Work in part ' + arch)
        print('\n========== Work in part ' + arch, file=log)
        # Quitamos la extensión
        arch_s, _ = os.path.splitext(arch)
        # Obtenemos sufijo
        sufix = arch_s[arch_s.find(symbol):]
        origin_dict = load_obj(dest_folder + '/' + arch, fast=True)
        pipeline_dict_features(origin_dict, sufix, cpu_c,
                                 dest_folder, log, use_joblib)
    log.close()

    # print('==================================================')
    # print('========== Procesando embeddings')

    
    # graph_version = 'med'
    # log = open(os.path.join(dest_folder, 'log_embeddings.txt'), 'w+')
    # lst_arch = read_parts('sparse_raw_dict_' + graph_version, dest_folder,
    #                       symbol)
    # print('Número de partes: ', len(lst_arch))
    # print(lst_arch)
    # print('Número de partes: ', len(lst_arch), file=log)
    # print(lst_arch, file=log)

    # # ===== Split dict in parts
    # for arch in lst_arch:
    #     print('\n========== Work in part ' + arch)
    #     print('\n========== Work in part ' + arch, file=log)
    #     # Quitamos la extensión
    #     arch, _ = os.path.splitext(arch)
    #     # Obtenemos sufijo
    #     sufix = arch[arch.find(symbol):]
    #     origin_dict = load_obj(dest_folder + '/' + arch, fast=True)
    #     pipeline_dict_embeddings(origin_dict, graph_version, sufix, cpu_c,
    #                              dest_folder, log, use_joblib)

    # log.close()


def pipeline_dict_embeddings(sparse_raw, graph_version, sufix, cpu_c,
                             dest_folder, log, use_joblib):
    print('Cores: ', cpu_c, file=log)

    print('Processing to word2vec dict...')
    dest_file = 'word2vec_dict' + '_' + graph_version + sufix
#     w2v_path = './embeddings/GoogleNews-vectors-negative300.bin'
#     function_args = \
#         {'model': KeyedVectors.load_word2vec_format(w2v_path, binary=True)}
    function_args = \
        {'model': api.load('word2vec-google-news-300')}
    word2vec = \
        dict_to_dict(sparse_raw, graph_sparse_raw_to_embeddings, cpu_c,
                     dest_folder, dest_file, log, function_args, use_joblib,
                     count_flag=True)
    del word2vec

    print('Processing to fasttext dict...')
    dest_file = 'fasttext_dict' + '_' + graph_version + sufix
    function_args = \
        {'model': api.load('fasttext-wiki-news-subwords-300')}
    fasttext = \
        dict_to_dict(sparse_raw, graph_sparse_raw_to_embeddings, cpu_c,
                     dest_folder, dest_file, log, function_args, use_joblib,
                     count_flag=True)
    del fasttext

    print('Processing to glove dict...')
    dest_file = 'glove_dict' + '_' + graph_version + sufix
    function_args = \
        {'model': api.load('glove-wiki-gigaword-300')}
    glove = \
        dict_to_dict(sparse_raw, graph_sparse_raw_to_embeddings, cpu_c,
                     dest_folder, dest_file, log, function_args, use_joblib,
                     count_flag=True)
    del glove

    # print('Processing to sense2vec dict...')
    # dest_file = 'sense2vec_dict' + '_' + graph_version + sufix
    # function_args = dict()
    # sense2vec = \
        # dict_to_dict(sparse_raw, graph_sparse_raw_to_sense2vec, cpu_c,
                     # dest_folder, dest_file, log, function_args)
    # del sense2vec


def pipeline_dict_features(parsed_dict, sufix, cpu_c, dest_folder, log,
                           use_joblib):
    print('Cores: ', cpu_c, file=log)

    # ===== Transform to parsed_dict
    print('Processing to text_feat_dict...')
    dest_file = 'text_feat_dict' + sufix
    function_args = dict()
    text_feat_dict = dict_to_dict(parsed_dict, text_parsed_to_features, cpu_c,
                                  dest_folder, dest_file, log, function_args,
                                  use_joblib)

# ============================================================
# ============================== leerpickle functions ==========

def part_pkl(dest_folder, new_files_prefix, d, element_num, use_joblib=None):
    items = sorted(d.items())

    data = [dict(items[x: x + element_num])
            for x in range(0, len(d), element_num)]
    for n in range(len(data)):
        save_obj(data[n], os.path.join(dest_folder,
                                       new_files_prefix + f'{n:02}').replace("\\","/"),
                 use_joblib=use_joblib)

def read_parts(file_name, dest_folder, symbol):
    lst_arch = os.listdir(dest_folder)
    new_files_prefix = file_name + symbol
    prefix_len = len(new_files_prefix)
    lst_arch = [x for x in lst_arch if x[:prefix_len] == new_files_prefix]
    lst_arch = sorted(lst_arch)
    return lst_arch


# ============================================================
# ============================== Test functions ==========

def main():
    #Estos metodos construye los textos a grafos 
    pipeline_dict_main() 
    separate_sparse_raw() 


if __name__ == "__main__":
    main()
