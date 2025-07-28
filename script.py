#!/usr/bin/python3

# Данный скрипт создан только для ознакомления. Я не могу гарантировать, что информация, которую он выдаст, окажется верной.
# Информация берется с сайта abit.miet.ru и является общедоступной

import requests
import json
import os

subms = [i for i in range (1, 60, 1)]
extras = [354, 355, 356]
subms.extend(extras)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json"
}

params_key = "parametrs"
params_subkey = "head_columns"
main_key = "applications"
name_key = "title"
cols_key = 'columns'

places = "Количество бюджетных мест"

abit = "Абитуриент"
uuid = "Номер личного дела"
permission = "Согласие на зачисление"
contract = "Наличие договора"
surpass = "БВИ"
score = "Сумма баллов"
priority = "Приоритет"

folder_name = "abit_lists"
files = []

os.makedirs(folder_name, exist_ok=True)

def parse_submissions():
  for i in range(1, 60, 1):
    if i < 10:
      url = f"https://abit.miet.ru/data/public/bak/basic/submitted/00000000{i}.json"
    elif i < 100:
      url = f"https://abit.miet.ru/data/public/bak/basic/submitted/0000000{i}.json"
    elif i < 1000:
      url = f"https://abit.miet.ru/data/public/bak/basic/submitted/000000{i}.json"

    response = requests.get(url, headers=headers)
    if not response:
      continue

    data = response.json()

    if len(data[main_key]) == 0:
      continue

    name = data[params_key][name_key].split('<br>')[1].split(' ', maxsplit=1)[1]
    files.append(name)

    with open(folder_name + "/" + name + ".json", 'w', encoding='utf-8') as file:
      json.dump(data, file, ensure_ascii=False, indent=4)

  print("Data parsing finished")

parse_submissions()

abits_data = {}
places_data = {}

for name in files:
  with open(folder_name + "/" + name + ".json", "r") as file:
    data = json.load(file)

    places_data[name] = data[params_key][params_subkey][0][1]

    uuid_idx = None
    permission_idx = None
    surpass_idx = None
    score_idx = None
    priority_idx = None

    for idx, dic in enumerate(data[params_key][cols_key]):

      if 'Номер личного дела' in dic.values():
          uuid_idx = idx
      if 'Согласие на зачисление' in dic.values() or 'Наличие договора' in dic.values():
          permission_idx = idx
      if 'БВИ' in dic.values():
          surpass_idx = idx
      if 'Сумма баллов' in dic.values():
          score_idx = idx
      if 'Приоритет' in dic.values():
          priority_idx = idx

    for val in data[main_key]:
      perm = False if val[permission_idx] is None else True
      if surpass_idx is not None:
        surp = False if val[surpass_idx] is None else True
      if surp:
        val[score_idx] = 1000 #условность, чтобы не усложнять сортировку
      if abits_data.get(val[uuid_idx]) is None:
        abits_data[val[uuid_idx]] = {name: {permission: perm, score: val[score_idx], priority: val[priority_idx], surpass: surp}}
      else:
        abits_data[val[uuid_idx]][name] = {permission: perm, score: val[score_idx], priority: val[priority_idx], surpass: surp}

with open("abits_data.json", 'w', encoding='utf-8') as file:
  json.dump(abits_data, file, ensure_ascii=False, indent=4)

def sort_abits(abits_data):
  for applicant in abits_data.values():

    sorted_directions = dict(sorted(
        applicant.items(),
        key=lambda item: item[1][priority]
    ))

    applicant.clear()
    applicant.update(sorted_directions)

  return abits_data

# Удаляем тех, у кого нет приоритета 1. Почему-то есть люди, у которых приоритеты
# 2, 3, 4... но при этом приоритета 1 нет. 
def clean_abits(abits_data):
  uids = list(abits_data.keys())
  uids_len = len(uids)
  i = 0
  while i < uids_len:
    dirs = list(abits_data[uids[i]].keys())
    first_dir = abits_data[uids[i]][dirs[0]]
    if first_dir[priority] != 1:
      del abits_data[uids[i]]
      uids.pop(i)
      uids_len -= 1
    else:
      i += 1
  
  return abits_data

abits_data = sort_abits(abits_data)
abits_data = clean_abits(abits_data)

with open('data.json', 'w', encoding='utf-8') as file:
    json.dump(abits_data, file, ensure_ascii=False, indent=4)

result_data = {}

def sort_res(result_data, dir):

  _items = result_data[dir]

  sorted_dir = dict(sorted(
      _items.items(),
      key=lambda item: item[1][score],
      reverse=True
  ))

  result_data[dir].clear()
  result_data[dir].update(sorted_dir)

  return result_data

def add_applicant(abits_data, result_data, applicant):
  for dir in abits_data[applicant].keys():
    if not abits_data[applicant][dir][permission]:
      return
    plcs = places_data[dir]
    subdata = result_data.get(dir)
    if subdata is None:
      result_data[dir] = {applicant: abits_data[applicant][dir]}
      abits_data[applicant].pop(dir)
      break
    else:
      if len(subdata.keys()) < plcs:
        result_data[dir][applicant] = abits_data[applicant][dir]
        result_data = sort_res(result_data, dir)
        abits_data[applicant].pop(dir)
        break
      else:
        _items = list(result_data[dir].items())
        if abits_data[applicant][dir][score] < _items[-1][1][score]:
          continue
        else:
          deleted = _items[len(_items) - 1]
          _items[-1] = (applicant, abits_data[applicant][dir])
          _items = dict(_items)
          result_data[dir].clear()
          result_data[dir].update(_items)
          result_data = sort_res(result_data, dir)
          abits_data[applicant].pop(dir)
          add_applicant(abits_data, result_data, deleted[0])
          break



for applicant in abits_data.keys():
  add_applicant(abits_data, result_data, applicant)

with open('res_data.json', 'w', encoding='utf-8') as file:
    json.dump(result_data, file, ensure_ascii=False, indent=4)

def print_res(dir):
  #print(f"Предварительные конкурсные списки по направлению {dir}, количество бюджетных мест: {places_data[dir]}")
  if result_data.get(dir) is not None:
    pass_score = list(result_data[dir].values())[len(result_data[dir].values()) - 1][score]
    #print(f"Предварительный проходной балл: {pass_score}")
    #print(json.dumps(result_data[dir], indent=4, ensure_ascii=False))
    print(f"{dir} : {pass_score}")

for val in places_data.keys():
  print_res(val)
