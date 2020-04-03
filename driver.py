import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
import random
import sys
import os
import time
import heapq

def generate_example(means_x, means_y, num_points, prob_file, plot=False):
	num_clusters = len(means_x)
	colors = cm.rainbow(np.linspace(0, 1, len(means_x)))
	cluster = 0
	x = []
	y = []
	if(plot):
		plt.subplot(1, 2, 1)
		plt.xlim(0, num_clusters*3+5)
		plt.ylim(0, num_clusters*3+5)

	for mx, my, c in zip(means_x, means_y, colors):
		x.append(np.random.normal(mx, 1, num_points))
		y.append(np.random.normal(my, 1, num_points))
		if(plot):
			plt.scatter(x[cluster], y[cluster], color=c)
		cluster += 1

	if(plot):
		plt.scatter(means_x, means_y, color='black', marker='x')
	x.append(np.random.rand(num_points*num_clusters) * num_clusters * 3)
	y.append(np.random.rand(num_points*num_clusters) * num_clusters * 3)
	if(plot):
		plt.scatter(x[cluster], y[cluster], color='black')

	num_data_points = num_points * num_clusters * 2
	data_points_x = []
	data_points_y = []
	clusters = []
	proximity = []
	cluster = 0
	for xc,yc in zip(x,y):
		data_points_x.extend(xc)
		data_points_y.extend(yc)
		if(cluster == num_clusters):
			clusters.extend([cluster] * num_points * num_clusters)
		else:
			clusters.extend([cluster] * num_points)
		cluster += 1
	#print(len(clusters))

	for xc, yc in zip(data_points_x, data_points_y):
		dist = []
		for mx, my in zip(means_x, means_y):
			dist.append(abs(xc-mx)+abs(yc-my))
		rank = heapq.nlargest(num_clusters, range(len(dist)), key=dist.__getitem__)
		proximity.append(rank)

	data = list(zip(data_points_x, data_points_y, clusters, proximity))
	random.shuffle(data)
	data_points_x, data_points_y, clusters, proximity = zip(*data)
	#print(clusters)

	prob = open(prob_file, "w")
	prob.write(str(num_data_points) + "\n")
	for i in range(num_data_points, 0, -1):
		for j in range(i-1, 0, -1):
			prob.write(str(i) + " " + str(j) + " ")
			if(clusters[i-1] == clusters[j-1]):
				if(clusters[i-1] != num_clusters):	
					score = pow(num_clusters, 3)
					prob.write(str(score) + "\n")
				else:
					prob.write("1\n")
			else:
				if(clusters[i-1] == num_clusters):
					score = pow(proximity[i-1].index(clusters[j-1]), 2)
				elif(clusters[j-1] == num_clusters):
					score = pow(proximity[j-1].index(clusters[i-1]), 2)
				else:
					score = -1 * pow(num_clusters, 3)
				prob.write(str(score)+"\n")


	assignment = {
		1 : []
	}
	index = 1
	for i in clusters:
		if(i+1 in assignment):
			assignment[i+1].append(index)
		else:
			assignment[i+1] = [index]
		index += 1

	#print("Problem:")
	#print(assignment)
	data = {
		"plot" : plt,
		"x"	   : data_points_x,
		"y"	   : data_points_y,
		"clusters" : clusters,
		"assignment" : assignment
	}
	return data


def post_processing(soln_file, num_points, data, plot=False):
	cost = 0
	with open(soln_file) as solution:
		line = solution.readline()
		while(line):
			if(line[0] == 'o'):
				cost = line[2]
			elif(line[0] == 'v'):
				assignment = line[2:-1]
			line = solution.readline()

	assignment = assignment.split(' ')
	sat_soln = list(map(int, assignment))

	num_variables = len(sat_soln)
	num_data_points = num_points

	clusters = {
		1 : [num_data_points]
	}
	point_assignments = {
		num_data_points : 1
	}

	base_point = num_data_points
	base_point_cluster = point_assignments[base_point]
	current_point = num_data_points-1
	max_cluster = 1
	for i in sat_soln:
		#print("Base: " + str(base_point))
		#print("Current: " + str(current_point))
		if(i > 0):
			if(current_point in point_assignments):
				clusters[point_assignments[current_point]].remove(current_point)
			clusters[base_point_cluster].append(current_point)
			point_assignments[current_point] = base_point_cluster
		else:
			if(not(current_point in point_assignments)):
				clusters[max_cluster+1] = [current_point]
				point_assignments[current_point] = max_cluster+1
				max_cluster = max_cluster+1
		if(current_point == 1):
			base_point = base_point-1
			base_point_cluster = point_assignments[base_point]
			current_point = base_point-1			
		else:
			current_point = current_point-1
		#print(point_assignments)
		#print(clusters)
		#print("------")


	for cluster in list(clusters):
		if(clusters[cluster] == []):
			del clusters[cluster]

	if(plot):
		num_clusters = len(clusters)
		clusters_points = clusters.values()
		colors = cm.rainbow(np.linspace(0, 1, num_clusters*3))
		data['plot'].subplot(1,2,2)
		data['plot'].xlim(0, num_clusters*3+5)
		data['plot'].ylim(0, num_clusters*3+5)
		for c, color in zip(clusters_points, colors[num_clusters+1:]):
			x = [data['x'][i-1] for i in c]
			y = [data['y'][i-1] for i in c]
			data['plot'].scatter(x, y, color=color)

	#print("Solution:")
	#print(clusters)
	#print("# Clusters = " + str(len(clusters)))
	#print("Cost = " + cost)
	data['cost'] = cost
	return data


def main(solver_path, plot=False):
	clusters_start = 2 
	clusters_end = 8
	clusters_step = 1

	num_points_start = 5
	num_points_end = 30
	num_points_step = 5

	log = open("log", "w")

	print((16*7+8) * "-")
	log.write(((16*7+8) * "-") + "\n")

	print('|%-16s|%-16s|%-16s|%-16s|%-16s|%-16s|%-16s|' % ("NUM CLUSTERS", "NUM POINTS", "VARIABLES", "CLAUSES", "COST", "SOLVER TIME (S)", "ENC TIME (S)"))
	log.write(('|%-16s|%-16s|%-16s|%-16s|%-16s|%-16s|%-16s|' % ("NUM CLUSTERS", "NUM POINTS", "VARIABLES", "CLAUSES", "COST", "SOLVER TIME (S)", "ENC TIME (S)")) + "\n")

	print((16*7+8) * "-")
	log.write(((16*7+8) * "-") + "\n")

	n = num_points_start
	for c in range(clusters_start, clusters_end+1, clusters_step):
		# Choose random mean values for the points in x and y dimensions
		mu_x = np.random.randint(3*c, size=c) + 2
		mu_y = np.random.randint(3*c, size=c) + 2
		while(n <= num_points_end):
			# Generate test case
			data = generate_example(mu_x, mu_y, n, 'problem', False)
			# Call the encoding C++ executable for the generated test case
			os.system('rm encoding_log')
			os.system('./encode_clustering problem encoding >> encoding_log')
			# Call the solver specified by the path for the encoded problem
			os.system('rm solution')
			start = time.time()
			os.system(solver_path + ' encoding >> solution')
			end = time.time()
			solver_time = end - start
			# Post-process the solver solution to verify correctness
			data = post_processing('solution', c * n * 2, data)
			if(plot):
				data['plot'].show()
			# Parse the runtime summary file
			with open('./rpt') as rpt:
				line = rpt.readline()
				while(line):
					if(line[0] == 'v'):
						variables = line[2:-1]
					elif(line[0] == 'c'):
						clauses = line[2:-1]
					elif(line[0] == 't'):
						encode_time = int(line[2:-1])
					line = rpt.readline()
			os.system('rm rpt')
			# Print result
			print('|%-16s|%-16s|%-16s|%-16s|%-16s|%-16s|%-16s|' % (c, n, variables, clauses, data['cost'], "%.2f" % solver_time, 1.0*encode_time/1000000))
			log.write(('|%-16s|%-16s|%-16s|%-16s|%-16s|%-16s|%-16s|' % (c, n, variables, clauses, data['cost'], "%.2f" % solver_time, 1.0*encode_time/1000000)) + "\n")
			n += num_points_step
		n = num_points_start

	print((16*7+8) * "-")
	log.write(((16*7+8) * "-") + "\n")


solver_path = '/mnt/d/PhD/Courses/CSC2512/a2/csc2512_a2/maxino2018/bin/maxino-static'
main(solver_path)