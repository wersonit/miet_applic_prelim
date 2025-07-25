#!/usr/bin/python3

# Данный скрипт создан только для ознакомления. Я не могу гарантировать, что информация, которую он выдаст, окажется верной.
# Информация берется с сайта abit.miet.ru и является общедоступной

import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json"
}

main_data = {}
places_data = {}

abit = "Абитуриент"
score = "Сумма баллов"
priority = "Приоритет"
permission = "Согласие на зачисление"
places = "Количество бюджетных мест"
surpass = "БВИ"

urls = {}

for i in range(1, 31, 1):
  if i < 10:
    url = f"https://abit.miet.ru/data/public/bak/basic/submitted/00000000{i}.json"
  else:
    url = f"https://abit.miet.ru/data/public/bak/basic/submitted/0000000{i}.json"

  response = requests.get(url, headers=headers)
  if not response:
    continue

  data = response.json()

  main_key = "applications"
  if len(data[main_key]) == 0:
    continue

  params_key = "parametrs"
  name = data[params_key]['title']
  if "Бюджет" not in name:
    continue

  name = name.split('<br>')[1].split(' ', maxsplit=1)[1]

  params_subkey = "head_columns"
  places_data[name] = data[params_key][params_subkey][0][1]

  uuid_idx = None
  permission_idx = None
  surpass_idx = None
  score_idx = None
  priority_idx = None

  cols_key = 'columns'
  for idx, dic in enumerate(data[params_key]['columns']):
    
    if 'Номер личного дела' in dic.values():
        uuid_idx = idx
    if 'Согласие на зачисление' in dic.values(): # or 'Наличие договора' in dic.values():
        permission_idx = idx
    if 'БВИ' in dic.values():
        surpass_idx = idx
    if 'Сумма баллов' in dic.values():
        score_idx = idx
    if 'Приоритет' in dic.values():
        priority_idx = idx

  for val in data[main_key]:
    perm = False if val[permission_idx] is None else True
    surp = False if val[surpass_idx] is None else True
    if surp:
      val[score_idx] = 1000 #условность, чтобы не усложнять сортировку
    if main_data.get(val[uuid_idx]) is None:
      main_data[val[uuid_idx]] = {name: {permission: perm, score: val[score_idx], priority: val[priority_idx], surpass: surp}}
    else:
      main_data[val[uuid_idx]][name] = {permission: perm, score: val[score_idx], priority: val[priority_idx], surpass: surp}

def sort_main(main_data):
  for applicant in main_data.values():

    sorted_directions = dict(sorted(
        applicant.items(),
        key=lambda item: item[1]["Приоритет"]
    ))

    applicant.clear()
    applicant.update(sorted_directions)

  return main_data

main_data = sort_main(main_data)

# _main_data = main_data.copy()

# with open('data.json', 'w', encoding='utf-8') as file:
#     json.dump(main_data, file, ensure_ascii=False, indent=4)

result_data = {}

def sort_res(result_data, dir):

  _items = result_data[dir]

  sorted_dir = dict(sorted(
      _items.items(),
      key=lambda item: item[1]["Сумма баллов"],
      reverse=True
  ))

  result_data[dir].clear()
  result_data[dir].update(sorted_dir)

  return result_data

def add_applicant(main_data, result_data, applicant):
  for dir in main_data[applicant].keys():
    if not main_data[applicant][dir][permission]:
      return
    plcs = places_data[dir]
    subdata = result_data.get(dir)
    if subdata is None:
      result_data[dir] = {applicant: main_data[applicant][dir].copy()}
      main_data[applicant].pop(dir)
      break
    else:
      if len(subdata.keys()) < plcs:
        result_data[dir][applicant] = main_data[applicant][dir].copy()
        result_data = sort_res(result_data, dir)
        main_data[applicant].pop(dir)
        break
      else:
        _items = list(result_data[dir].items())
        if main_data[applicant][dir][score] < _items[len(_items) - 1][1][score]:
          continue
        else:
          deleted = _items[len(_items) - 1]
          _items[len(_items) - 1] = (applicant, main_data[applicant][dir].copy())
          _items = dict(_items)
          result_data[dir].clear()
          result_data[dir].update(_items)
          result_data = sort_res(result_data, dir)
          main_data[applicant].pop(dir)
          add_applicant(main_data, result_data, deleted[0])
          break



for applicant in main_data.keys():
  add_applicant(main_data, result_data, applicant)

# with open('res_data.json', 'w', encoding='utf-8') as file:
#     json.dump(result_data, file, ensure_ascii=False, indent=4)

def print_res(dir):
  #print(f"Предварительные конкурсные списки по направлению {dir}, количество бюджетных мест: {places_data[dir]}")
  pass_score = list(result_data[dir].values())[len(result_data[dir].values()) - 1][score]
  #print(f"Предварительный проходной балл: {pass_score}")
  #print(json.dumps(result_data[dir], indent=4, ensure_ascii=False))
  print(f"{dir} : {pass_score}")

for val in places_data.keys():
  print_res(val)
