import string
import datetime
import time
import timeit

class RawProbability:
	# A raw probability roughly corresponds to a possible world, where each world is a set of 
	# propositions true at that world. Each proposition p_i is true with probability equal to values[i]. 
	# The probability for the possible world w is simply the product of the probabilities of all true 
	# statements at w multiplied by the product of of the probabilities of the negations of all false 
	# statements at w.
	def __init__(self, bools, values):
		self.length = len(values) 	# Number of propositions used to determine the possible world
		self.values = values 		# Value of the probabilities of each of the statements
		self.bools = bools 			# List of booleans stating which statements are true at this world
		self.value = 1 				# Probability that this world will occur
		i = 0
		for v in values:
			if (self.bools[i]):
				self.value *= v
			else:
				self.value *= 1 - v
			i += 1
	def print_raw(self):
		print "Value: " + str(self.value) + "," + str(self.bools)
		
	def __eq__(self, rp):
		equal = True
		i = 0
		for b in self.bools:
			if b != rp.bools[i]:
				equal = False
			i += 1
		return equal
	
	def __hash__(self):
		total = 0
		i = 0
		for b in self.bools:
			if b is True:
				total += 2**i
			i += 1
		return hash(total)
		
class ProbabilitySet:
	# A Probability Set is simply of a set of possible worlds.
	def __init__(self, elements):
		self.elements = set(elements)
		
	def compute_probability(self):
		# The probability of a probability set is simply the sum of the probabilities of the possible worlds
		# contained within that set.
		value = 0
		for ele in self.elements:
			value += ele.value
		return value
	
	def union(self, s):
		return ProbabilitySet(self.elements.union(s.elements))
	
	def intersection(self, s):
		return ProbabilitySet(self.elements.intersection(s.elements))
		
	def print_set(self):
		print "Probability: " + str(self.compute_probability())
		
	def print_debug(self):
		print "Probability: " + str(self.compute_probability())
		for element in self.elements:
			element.print_raw()
		
def generate_raw_probabilities(skip_index, i, length, elements, bools):
	if i == skip_index:
		return generate_raw_probabilities(skip_index, i+1, length, elements, bools)
	elif i == length:
		return [RawProbability(bools, elements)]
	else:
		bools1 = bools[:]
		bools2 = bools[:]
		bools1[i] = True
		bools2[i] = False
		temp = []
		temp.extend(generate_raw_probabilities(skip_index, i+1, length, elements, bools1))
		temp.extend(generate_raw_probabilities(skip_index, i+1, length, elements, bools2))
		return temp

def generate_probability_sets(elements):
	i = 0
	sets = []
	for element in elements: # Generate raw probabilities
		bools = elements[:]
		bools[i] = True
		length = len(elements)
		my_list = generate_raw_probabilities(i, 0, length, elements, bools)
		sets.append(ProbabilitySet(my_list))
		i += 1
	return sets

def main():
	print "Starting Tests..."
	############ Test Cases ##########
	elements = [0.25, 0.4, 0.6]
	sets = generate_probability_sets(elements)
	
	print "Elements:"
	print elements
	print "Probability Sets:"
	for s in sets:
		s.print_debug()
	
	print "Test for f0 + f1:"
	ps = sets[0].union(sets[1])
	ps.print_debug()
	
	print "Test for f1 * f2:"
	ps2 = sets[1].intersection(sets[2])
	ps2.print_debug()
	
	print "Test for f0 + f1 + f2:"
	ps3 = ps.union(sets[2])
	ps3.print_debug()
	
	############ END OF TESTS ##########
	
	# Failure groups f0 - f6
	failure_groups = [0.01, 0.1, 0.2, 0.15, 0.4, 0.05, 0.02]
	f = generate_probability_sets(failure_groups)
	
	# A = {f0,f1,f2,f4}
	A = f[0].union(f[1]).union(f[2]).union(f[4])
	print "Probability for A:"
	A.print_set()
	# B = {f0,f2,f3,f5}
	B = f[0].union(f[2]).union(f[3]).union(f[5])
	print "Probability for B:"
	B.print_set()
	# C = {f0,f1,f3,f6}
	C = f[0].union(f[1]).union(f[3]).union(f[6])
	print "Probability for C:"
	C.print_set()
	
	print "Probability for A AND B AND C: "
	total = A.intersection(B).intersection(C)
	total.print_set()
	
if __name__ == '__main__':
	t = timeit.Timer(main)
	print "%.2f sec" % t.timeit(number=1)
#	main()