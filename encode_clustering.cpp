#include <iostream>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <utility>
#include <vector>
#include <stdlib.h>
#include <chrono>

using namespace std;
using namespace std::chrono;

// Hash function for pair data type
struct hash_pair { 
    template <class T1, class T2> 
    size_t operator()(const pair<T1, T2>& p) const
    { 
        auto hash1 = hash<T1>{}(p.first); 
        auto hash2 = hash<T2>{}(p.second); 
        return hash1 ^ hash2; 
    } 
};

unsigned int factorial(unsigned int n){
	if(n == 0)
		return 1;
	else
		return n * factorial(n-1);
}

void generate_hard_clauses(ofstream *output_file, unsigned int num_data_points, int top,
	unordered_map<pair<unsigned int, unsigned int>, unsigned int, hash_pair> *variable_lut){
	unsigned int num_hard_clauses = 0;
	pair<unsigned int, unsigned int> q1, q2, q3;
	for(unsigned int i = 1; i <= num_data_points; i++){
		for(unsigned int j = 1; j <= num_data_points; j++){
			for(unsigned int k = 1; k <= num_data_points; k++){
				if((i == j) || (j == k) || (i == k))
					continue;
				q1.first = (j>i)? j:i; q1.second = (j>i)? i:j;
				q2.first = (k>j)? k:j; q2.second = (k>j)? j:k;
				q3.first = (k>i)? k:i; q3.second = (k>i)? i:k;
				//(*output_file) <<  top << " -" << (num_data_points*i)+j+1 << " -" << (num_data_points*j)+k+1
				//	<< " " << (num_data_points*i)+k+1 << " 0" << endl;
				(*output_file) <<  top << " -" 
					<< variable_lut->at(q1) << " -" 
					<< variable_lut->at(q2) << " " 
					<< variable_lut->at(q3) << " 0" << endl;
				num_hard_clauses++;
			}
		}
	}

}

void generate_soft_clauses(ofstream *output_file, unsigned int num_data_points, 
		unordered_map<pair<unsigned int, unsigned int>, int, hash_pair> *similarities,
		unordered_map<pair<unsigned int, unsigned int>, unsigned int, hash_pair> *variable_lut){
	unordered_map<pair<unsigned int, unsigned int>, int, hash_pair>::iterator it = similarities->begin();
 	unsigned int i, j;
 	int score;
 	pair<unsigned int, unsigned int> q1, q2;
	while (it != similarities->end()){
		i = it->first.first;
		j = it->first.second;
		score = it->second;
		if(i > j){
			q1.first = i; q1.second = j;
		} else {
			q1.first = j; q1.second = i;
		}

		if(score > 0) {
			(*output_file) << score << " " << variable_lut->at(q1) << " 0" << endl;
		} else {
			(*output_file) << abs(score) << " -" << variable_lut->at(q1) << " 0" << endl;
		}
 
		it++;
	}
}


int main (int argc, char* argv[]) {
	// Open constraints file
	ifstream input_file;
	string line;
	input_file.open(argv[1]);
	if(!input_file){
		cout << "[ERROR] Unable to open input file" << endl;
		return 0;
	}

	// Get number of data points in the problem
	unsigned int num_data_points, num_hard_clauses, num_soft_clauses;
	if(getline(input_file, line)){
		num_data_points = stoi(line);
		//cout << "[INFO] There is a total of " << num_data_points << " data points to cluster." << endl;
	} else {
		cout << "[ERROR] Input file is empty" << endl;
		return 0;
	}
	num_hard_clauses = (num_data_points)*(num_data_points-1)*(num_data_points-2);
	//cout << num_hard_clauses << " hard clause(s)." << endl;
	num_soft_clauses = 0;

	// Parse all similarity scores into a hash map (pair of points -> score)
	unordered_map<pair<unsigned int, unsigned int>, int, hash_pair> similarities;
	bool pass;
	unsigned int p1, p2;
	int total_score = 0;
	int score;
	stringstream linestream;
	while(getline(input_file, line)){
		linestream.str(line);
		linestream >> p1;
		linestream >> p2;
		linestream >> score;
		pair<unsigned int, unsigned int> point (p1, p2);
		similarities[point] = score;
		total_score += abs(score);
		//cout << "<" << point.first << "," << point.second << ">: " << score << endl;
		linestream.clear();
		num_soft_clauses++;
	}

	// Create variable look-up table
	unsigned int num_variable = 1;
	unordered_map<pair<unsigned int, unsigned int>, unsigned int, hash_pair> variable_lut;
	for(int i = num_data_points; i > 1; i--){
		for(int j = i-1; j >= 1; j--){
			pair<unsigned int, unsigned int> point (i, j);
			variable_lut[point] = num_variable;
			num_variable++;
		}
	}

	// Generate the encoding file
	ofstream output_file;
	output_file.open(argv[2]);
	output_file << "p wcnf " << num_variable-1 << " " << num_hard_clauses+num_soft_clauses 
		<< " " << total_score+1 << endl;
	auto start = high_resolution_clock::now();
	generate_hard_clauses(&output_file, num_data_points, total_score+1, &variable_lut);
	generate_soft_clauses(&output_file, num_data_points, &similarities, &variable_lut);
	auto stop = high_resolution_clock::now(); 
	auto encoding_time = duration_cast<microseconds>(stop - start);
	output_file.close();

	ofstream rpt;
	rpt.open("rpt");
	rpt << "v " << num_variable-1 << endl;
	rpt << "c " << num_hard_clauses+num_soft_clauses << endl;
	rpt << "t " << encoding_time.count() << endl;
	rpt.close();
}
