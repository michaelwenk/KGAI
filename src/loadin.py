import json

with open('../data/chemotion-datadump-2023-12-13.jsonld') as file:
  content = json.load(file)

  keywords = set()
  keyword_list = list()

  # count = 0
  # limit = 1
  graph = content["@graph"]
  for graph_elem in graph:
    # print(graph_elem)
    for elem in graph_elem:
      # print(elem)
      if keywords.__contains__(elem) == False:
        keyword_list.append(elem)
      keywords.add(elem)
      if isinstance(elem, dict) or isinstance(elem, list):
        for elem2 in elem:
          # print(elem2)
          if keywords.__contains__(elem) == False:
            keyword_list.append(elem)
          keywords.add(elem2)
    # count = count + 1    
    # if count > limit:
    #   break  
    # print("count: " + str(count))
    
  print(keyword_list)
  filtered_keyword_list = list(filter(lambda x: not x.startswith("@"), keyword_list))
  print(filtered_keyword_list)
