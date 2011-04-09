class DNSQuery:
  def __init__(self, data):
    self.data = data
    self.domain=''

    opcode = (ord(self.data[2]) >> 3) & 15   # 4-bit Opcode: 0|1|2
    print "Opcode: ", opcode
    if opcode == 0:                     # standard query (QUERY)
      index = 12
      length = ord(self.data[index])
      print "Length: ", length
      while length != 0:
        self.domain += self.data[index+1:index+length+1]+'.'
        index += length+1
        length = ord(self.data[index])

    print "Domain: %s" % self.domain

  def respond(self, ip):
    response=''
    if self.domain:
      response += self.data[:2] + "\x81\x80"
      response += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'   # Questions and Answers Counts
      response += self.data[12:]                                         # Original Domain Name Question
      response += '\xc0\x0c'                                             # Pointer to domain name
      response += '\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'             # Response type, ttl and resource data length -> 4 bytes
      response += str.join('',map(lambda x: chr(int(x)), ip.split('.'))) # 4bytes of IP

      print response
      
    return response
