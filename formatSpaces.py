import re
import os
DEFAULT_SPACE = 2

PROCESS_GENERATE_REGEX = r'''(?six)[\ \t]*(?P<name>\w+)\s+(?P<notsurewhattocallthis>:[\ \t\w]+)
                              (?P<type>process|generate)
                              (?P<clock>[\ \t\w\(\)]+)?(?P<body>.*?)
                              (?P<ending>end\b(\s+(?P=type)))
                              (?P<end_name>\s+(?P=name))?
                              |^(?P<not_process_or_generate>[\ \t\w\S]*)'''
ARCH_REGEX = r'''(?six)
                (?P<type>architecture)\s+(?P<name>\w+)\s+(?:of)\s+(?P<entity_name>\w+)\s+is\n
                (?P<declarations>.*?)(?:begin)
                (?P<arch_body>.*?)
                (?P<ending>end\b(\s+(?P=name))?)\s*;'''

def get_max_length( data, index ) :
  d = max(data, key=lambda x: 0 if len(x) <= index else len(x[index]))
  # Return maybe an odd number so tabbing will look correct
  return len(d[index])+1

def check_length( length ) :
  if( length % DEFAULT_SPACE is not 0 ) :
    return length + DEFAULT_SPACE//2
  else :
    return length

def check_parentheses( data ) :
  return re.sub(r"(\S)\(", r'\1 (', data)

def generic_port( data, index, indent_level ):
  found = False
  new_index = index + 1
  data[index] = check_parentheses(data[index])
  generic_data = []

  # Put spaces for generic name
  data[index] = "{:{}}{}".format("", indent_level*DEFAULT_SPACE, data[index])

  while( not found ):
    # d = re.split(r"( )", data[new_index])
    d = data[new_index].split()
    generic_data.append(d)
    if ")" in data[new_index]:
      break
    new_index += 1

  maxspace = get_max_length(generic_data, 0)

  # Add spacing if max string length is not a modulo of DEFAULT_SPACE
  if( maxspace % DEFAULT_SPACE is not 0 ):
    maxspace += DEFAULT_SPACE//2

  # Add modified data back
  for i in range(len(generic_data)):
    # So we know that there has to be at least 3 items with a generic
    data_length = len( generic_data[i] )
    data_index = i + index + 1

    # Check for empty array, this means there there was a new line
    if not generic_data[i] :
      data[data_index] = "\n"
      continue

    # Check for the ending bracket
    if ")" in generic_data[i][0]:
      data[data_index] = "{:{}}{}".format("", DEFAULT_SPACE*indent_level, generic_data[i][0])
    else:
      data[data_index] = "{:{}}{:{}}".format( "", DEFAULT_SPACE*(indent_level+1), 
                                              generic_data[i][0], maxspace)

    # Print out the rest of the data if there is some
    if data_length > 1 :
      for j in range(1, data_length):
        data[data_index] += " {:{}}".format(generic_data[i][j], get_max_length(generic_data, j))

    # Add new line
    data[data_index] += "\n"
  return new_index + 1

  # data[index] = "{:{}} {} (\n".format("", indent_level*DEFAULT_SPACE, data[index].split()[0])

# def generic( data, index, indent_level )

def strip_lead_trail_spaces( data ):
  for index, item in enumerate(data):
    data[index] = item.strip(" \t").replace("\t", "{:{}}".format("", DEFAULT_SPACE))
    # data[index] = item.replace("\t", "{:{}}".format(" ", DEFAULT_SPACE))

def parse_declarations(data) : 
  # TODO: add support for parsing the following 
  # type, subtype, file, alias, component, attribute, function, procedure, configuration
  reParams = r'''(?six)\s*(?P<type>[constant|signal]\w+)[\ \t]*?
                  (?P<name>\w+)\s*:\s*
                  (?P<signal_type>\w+\([^\)]*\)?|\w+[\ \t]range[\ \t]+[\w\-\+]+[\ \t]+(?:(?:down)?to)[\ \t]+[\w\-\+]+|\w+)?
                  (?:[\ \t]*:=[\ \t]*(?P<init>.*?))?
                  (?:[\ \t]*;?[\ \t]*)
                  (?:--[\ \t]*(?P<comment>[^\n]*))?$|
                  (?:--[\ \t]*(?P<lineComment>[^\n]*))'''

  # Splitting on New line to perserve lines between text
  sp = re.split("\n", data)
  # Strip out leading spaces
  spStrip =[ x.strip() for x in sp]
  # rGroup = [[]] * len(spStrip)
  rGroup = []
  for x in spStrip:
    t = re.findall(reParams, x)
    rGroup.append( () if len(t) == 0 else t[0])
  
  # Remove last entry this is most likely a false new line from the last line in the string
  #   But make sure that this does not remove an entry if it has actual data.
  #   The only way that this can happen is if someone put begin on the same line
  #   as a signal definition.... which would be wrong
  if len(rGroup[len(rGroup)-1]) == 0 :
    rGroup.pop(len(rGroup)-1)

  rListSize = len(rGroup[0])
  length_list = [0] * rListSize

  for i in range(rListSize-2) :
    length_list[i] = check_length( get_max_length(rGroup, i) )

  new_data = ""
  for x in rGroup:
    string = ""
    # Make sure there is data
    if len(x) > 0 :
      # If index 6 is not Null then this is a full line comment, re print out
      if x[rListSize-1] :
        dashes = re.findall(r'''(?six)^[\-]*''', x[rListSize-1])
        if len(dashes[0]) > 0 :
          string = "{:{}}--{}".format("", DEFAULT_SPACE, x[rListSize-1])
        else :
          string = "{:{}}-- {}".format("", DEFAULT_SPACE, x[rListSize-1])
      else :
        string = "{:{}}{:{}}".format("", DEFAULT_SPACE, x[0], length_list[0])
        for i in range(1,rListSize) :
          if i == 4 :
            string = string.rstrip() + ";"
            if x[i]:
              # Calculate ending comment length
              tSum = 0
              for a in range(0,4):
                tSum += length_list[a]
              tSum += 7
              tSum = check_length(tSum)
              
              string = "{:{}}-- {}".format(string, tSum, x[i])
          elif x[i] :
            if i == 2 :
              string += ": "
            elif i == 3 :
              string += ":= "
          
            if i < 4 :
              string += "{:{}}".format(x[i], length_list[i])
        
    new_data += string + "\n"
  return new_data

def parse_arch_body(data) :
  return data

def format_body(data):
  # Search for declarations
  r = re.search(r'(?six).*?(?=begin)', data, flags=re.MULTILINE)
  span = r.span()
  s = r[0]
  new_data = parse_declarations(s)
  data = data[:span[0]] + new_data + data[span[1]:]
  # Parse everything after begin

  return data
  



def main():
  os.makedirs(os.path.dirname("output_files/"), exist_ok=True)
  indent_level = 0

  with open("test_files\\test.vhd", "r+" ) as file:
    file_data = file.read()

  # Scan for included libaries

  # Scan for entity definition

  oldParams = r'''(?six)(?P<type>architecture)\s+(?P<name>\w+)\s+of\s+(?P<entity>\w+)\s+is\n
                (?P<body>.*)(?P<ending>end\b(\s+(?P=name))?)\s*;'''
  # Scan for Architecture 
  r = re.search(ARCH_REGEX, file_data)
  body = r.group("declarations")
  body = body.replace("\t", '')

  
  print(len(body))
  span = r.span("declarations")
  body = parse_declarations(body)

  file_data = file_data[:span[0]] + body + file_data[span[1]:]

  new_file = open("output_files\\newVhdl.vhd", "w+")
  for line in file_data:
    new_file.writelines(line)
    # print(line, end=" ")
  new_file.close()



if __name__ == "__main__":
  main()