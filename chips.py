# ################################### INFO ##################################### #
# ChIp-seq analysis workflow 1.0
# Author: Amir Shams
# Email: amir.shams84@gmail.com
# ################################### IMPORTED LIBRARY ######################### #


import sys
import os
import argparse
import time
import multiprocessing
import platform
import logging as log
import itertools
import errno
import signal
import datetime
import traceback
import subprocess
import pandas
# ################################### GLOBAL VARIABLES ######################## #


CHECK_MARK = "OK"
FAILED_MARK = ":("
DEFAULT_INPUTDIR = "/INPUTDIR/"
DEFAULT_OUTPUTDIR = "/OUTPUTDIR/"
DEFAULT_INDEXDIR = "/INDEXDIR/"
DEFAULT_TESTDIR = "/TESTDIR/"
DEFAULT_EXECDIR = "/EXECDIR/"
DEFAULT_PROCESSORS = str(multiprocessing.cpu_count())
DEFAULT_PREFIX = "ChIps"
# ################################### EXECUTIONS ############################### #


def execute_functions(function_name, processors, outputdir, thread_type, func_mode, *args):
	list_of_pid = []
	list_of_stderr = []
	list_of_stdout = []
	if thread_type == 'fork':
		threads = int(processors) + 1
		processors = '1'
	elif thread_type == 'multi':
		threads = 2
	for thread in range(1, threads):
		pid_file = 'run.pid' + str(thread)
		stderr_file = 'stderr' + str(thread)
		stdout_file = 'stdout' + str(thread)
		run_pid = outputdir + pid_file
		stderr = outputdir + stderr_file
		stdout = outputdir + stdout_file
		flag = function_name(processors, outputdir, stderr, stdout, run_pid, *args)
		if flag is False:
			sys.exit(2)
		list_of_pid.append(pid_file)
		list_of_stderr.append(stderr_file)
		list_of_stdout.append(stdout_file)
	flag, stderr = process_monitor(list_of_pid, list_of_stderr, list_of_stdout, outputdir, threads, func_mode)
	if flag is False:
		print "Process monitor failed."
	else:
		pass
	return (True, stderr)


def process_monitor(pid_list, stderr_list, stdout_list, outputdir, threads, mode):

	finished_flag = False
	flag_list = {}
	for each_pid in pid_list:
		flag_list[each_pid] = False
	toolbar_width = threads
	sys.stdout.write("[%s]" % (" " * toolbar_width))
	sys.stdout.flush()
	sys.stdout.write("\b" * (toolbar_width + 1))  # return to start of line, after '['
	while finished_flag is False:
		for pid_file, stderr_file, stdout_file in itertools.izip(pid_list, stderr_list, stdout_list):
			f = open(outputdir + pid_file)
			the_pid = int(f.read().rstrip())
			if pid_exists(the_pid) is False:
				sys.stdout.write("OK")
				sys.stdout.flush()
				flag_list[pid_file] = True
				flag, stderr = validate_execution(stderr_file, stdout_file, outputdir, mode)
				if flag is False:
					sys.stdout.write(":(")
					report("[:()]")
					print "Error in result of this thread: ", str(the_pid)
					error("Error in result of this thread: " + str(the_pid))
					print "All generated threads killed."
					error("All generated threads killed.")
					kill_pid_list(pid_list, outputdir)
					#print stderr
					print "ABORTING!!!"
					report("ABORTING!!!")
					sys.exit(2)
			if False in flag_list.values():
				finished_flag = False
			else:
				finished_flag = True
		time.sleep(1)
	sys.stdout.write("\n")
	report("[OK]")
	return (True, stderr)


def pid_exists(pid):
	if pid < 0:
		return False
	if pid == 0:
		# According to "man 2 kill" PID 0 refers to every process
		# in the process group of the calling process.
		# On certain systems 0 is a valid PID but we have no way
		# to know that in a portable fashion.
		raise ValueError('invalid PID 0')
	try:
		os.kill(pid, 0)
	except OSError as err:
		if err.errno == errno.ESRCH:
			# ESRCH == No such process
			return False
		elif err.errno == errno.EPERM:
			# EPERM clearly means there's a process to deny access to
			return True
		else:
			# According to "man 2 kill" possible error values are
			# (EINVAL, EPERM, ESRCH)
			raise
	else:
		return True


def validate_execution(stderr, stdout, outputdir, mode):
	if mode == 'usearch':
		f = open(outputdir + stdout, 'rU')
		data = f.read()
		#print data
		if '---Fatal error---' in data or 'Invalid command line' in data:
			return (False, data)
		else:
			return(True, data)
	elif mode == 'mothur':
		f = open(outputdir + stdout, 'rU')
		data = f.read()
		if '[ERROR]:' in data:
			return (False, data)
		else:
			return(True, data)
	elif mode == 'mafft':
		f = open(outputdir + stdout, 'rU')
		data = f.read()
		if 'No such file or directory' in data or 'cannot open file' in data:
			return (False, data)
		else:
			return(True, data)


def kill_pid_list(pid_list, outputdir):
	for pid in pid_list:
		f = open(outputdir + pid)
		the_pid = int(f.read().rstrip())
		try:
			os.kill(the_pid, signal.SIGTERM)
		except OSError:
			pass
		print the_pid, "Killed!"
	return True


def execute(command, ** kwargs):
	assert isinstance(command, list), "Expected 'command' parameter to be a list containing the process/arguments to execute. Got %s of type %s instead" % (command, type(command))
	assert len(command) > 0, "Received empty list of parameters"
	retval = {
			"exitCode": -1,
			"stderr": u"",
			"stdout": u"",
			"execTime": datetime.timedelta(0),
			"command": None,
			"pid": None
		}
	retval["command"] = command
	log.info("::singleProcessExecuter > At %s, executing \"%s\"" % (datetime.datetime.now(), " ".join(command)))
	# print("::singleProcessExecuter > At %s, executing \"%s\"" % (datetime.datetime.now(), " ".join(parameter)))
	cwd = kwargs.get("cwd", os.getcwd())
	sheel = kwargs.get("shell", True)
	startDatetime = datetime.datetime.now()
	myPopy = subprocess.Popen(command, cwd=cwd, preexec_fn=os.seteuid(os.getuid()), shell=sheel, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
	retval["pid"] = myPopy.pid
	log.debug("::singleProcessExecuter > Command \"%s\" got pid %s" % (" ".join(command), myPopy.pid))
	try:
		retval["stdout"], retval["stderr"] = myPopy.communicate()
		myPopy.wait()
	except OSError, osErr:
		log.debug("::singleProcessExecuter > Got %s %s in myPopy.communicate() when trying get output of command %s. It is probably a bug (more info: http://bugs.python.org/issue1731717)" % (osErr, type(osErr), command[0]))
	except Exception, e:
		log.warn("::singleProcessExecuter > Got %s %s when trying to get stdout/stderr outputs of %s" % (type(e), e, " ".join(command)))
		log.debug("::singleProcessExecuter > Got %s %s when trying to get stdout/stderr outputs of %s. Showing traceback:\n%s" % (type(e), e, " ".join(command), traceback.format_exc()))
		raise
	retval["exitCode"] = myPopy.returncode
	retval["execTime"] = datetime.datetime.now() - startDatetime
	return retval
# ################################### UTILITIES ############################### #


def check_it_and_remove_it(filename, noreport=False):
	try:
		os.remove(filename)
		if noreport is False:
			pass
	except OSError:
		pass


def isFileExist(fname):
	# check the exitence/access/path of a file
	if os.path.isfile(fname) and os.path.exists(fname) and os.access(fname, os.R_OK):
		return True
	else:
		return False


def scandirs(path, container, ext_list, mode=None):
	# scan a spath and grab all files by specified extension
	for root, dirs, names in os.walk(path):
		for currentFile in names:
			path, absname, ext = split_file_name(currentFile)
			if mode is None:
			# Looking for exactly the same extension
				if ext in ext_list:
					container.append(os.path.join(root, currentFile))
			elif mode == 'multiple':
				for each_ext in ext_list:
					if ext in each_ext:
						container.append(os.path.join(root, currentFile))
			elif mode == 'partial':
				# when this extension is part of the actual extension of files
				for each_ext in ext_list:
					if each_ext in ext:
						container.append(os.path.join(root, currentFile))
	if len(container) < 1:
		return False
	return True


def split_file_name(file):
	path = os.path.dirname(file) + '/'
	name = os.path.basename(file)
	if '.' in name:
		ext = '.' + '.'.join(name.split('.')[1:])
		absname = name.split('.')[0]
	else:
		ext = 'no_extension'
		absname = name
	return (path, absname, ext)


def write_string_down(new_string, file_name):
	f = open(file_name, 'w')
	f.write(new_string)
	f.close()
	return True


def match_two_list(list_A, list_B):
	#
	return set(list_A) & set(list_B)


def get_extension(file_PATH):
	#Get Extension
	return file_PATH.split('.')[-1].lower()


def text_to_pandas_dataframe_converter(Text_File_PATH, Skiprows_Value=None, Index_Value=None):
	# ##########
	return pandas.read_table(Text_File_PATH, low_memory=False, encoding='utf-8', skip_blank_lines=True, error_bad_lines=False, skiprows=Skiprows_Value, index_col=Index_Value)
# ################################### LOGGING & REPORTING ##################### #


def error(report_string):
	f = open(report_file, "a")
	f.write('###############################  ERROR   ###################################\n')
	f.write(report_string)
	f.write("\n")
	f.write('############################################################################\n')
	f.close()


def report(report_string):
	f = open(report_file, "a")
	f.write(report_string.encode('utf8'))
	f.write("\n")
	f.close()
# ################################### OBJECTS ################################## #


class mothur_process:
	def __init__(self, mothur_input_dictionary):
		for var_name, var_value in mothur_input_dictionary.items():
			setattr(self, var_name, var_value)

	def build_mothur_command(self):
		space = " "
		string = ''
		if hasattr(self, 'nohup_in'):
			string += self.nohup_in + space
		string += self.mothur_exec_path + space + '"#set.dir(output=' + self.outputdir + ');' + space
		string += 'set.logfile(name=mothur.' + self.command + '.logfile);' + space
		string += 'set.current(processors=' + self.processors + ');' + space
		string += self.command + '('
		if hasattr(self, 'parameters') and len(self.parameters) > 0:
			for each_element in self.parameters:
				string += each_element
		string += ');"'
		if hasattr(self, 'nohup_out'):
			string += space + self.nohup_out
		if hasattr(self, 'pid_file'):
			string += ' echo $! > ' + self.pid_file
		report(string)
		print string
		return string

	def execute_mothur_command(self):
		exec_dict = {}
		exec_dict = self.execute([self.build_mothur_command()])
		if exec_dict['exitCode'] != 0:
			print "ERROR occurred!!!!"
			return (False, exec_dict)
		else:
			return(True, exec_dict)

	def execute(self, command, ** kwargs):
		assert isinstance(command, list), "Expected 'command' parameter to be a list containing the process/arguments to execute. Got %s of type %s instead" % (command, type(command))
		assert len(command) > 0, "Received empty list of parameters"
		retval = {
					"exitCode": -1,
					"stderr": u"",
					"stdout": u"",
					"execTime": datetime.timedelta(0),
					"command": None,
					"pid": None
				}
		retval["command"] = command
		log.info("::singleProcessExecuter > At %s, executing \"%s\"" % (datetime.datetime.now(), " ".join(command)))
		cwd = kwargs.get("cwd", os.getcwd())
		#user = kwargs.get("user", os.getuid)
		sheel = kwargs.get("shell", True)
		startDatetime = datetime.datetime.now()
		myPopy = subprocess.Popen(command, cwd=cwd, preexec_fn=os.seteuid(os.getuid()), shell=sheel, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
		retval["pid"] = myPopy.pid
		log.debug("::singleProcessExecuter > Command \"%s\" got pid %s" % (" ".join(command), myPopy.pid))
		try:
			retval["stdout"], retval["stderr"] = myPopy.communicate()
			myPopy.wait()
		except OSError, osErr:
			log.debug("::singleProcessExecuter > Got %s %s in myPopy.communicate() when trying get output of command %s. It is probably a bug (more info: http://bugs.python.org/issue1731717)" % (osErr, type(osErr), command[0]))
		except Exception, e:
			log.warn("::singleProcessExecuter > Got %s %s when trying to get stdout/stderr outputs of %s" % (type(e), e, " ".join(command)))
			log.debug("::singleProcessExecuter > Got %s %s when trying to get stdout/stderr outputs of %s. Showing traceback:\n%s" % (type(e), e, " ".join(command), traceback.format_exc()))
			raise
		retval["exitCode"] = myPopy.returncode
		retval["execTime"] = datetime.datetime.now() - startDatetime
		return retval
# ################################### MOTHUR FUNCTIONS ######################## #


def test_mothur(processors, outputdir, stderr, stdout, run_pid, mothur_exec_PATH):
	# test mothur to see if it is working and grab the version of mothur by scanning its output log
	mothur_input_dictionary = {}
	command = 'get.current'
	mothur_input_dictionary['command'] = command
	mothur_input_dictionary['mothur_exec_path'] = mothur_exec_PATH
	mothur_input_dictionary['processors'] = processors
	mothur_input_dictionary['outputdir'] = outputdir
	mothur_input_dictionary['nohup_in'] = 'nohup'
	mothur_input_dictionary['nohup_out'] = '> ' + stdout + ' 2> ' + stderr + ' & echo $! > ' + run_pid
	#parameter_list = []
	make_file_object = mothur_process(mothur_input_dictionary)
	exec_dict = {}
	flag, exec_dict = make_file_object.execute_mothur_command()
	if flag is False:
		print "[FATAL-ERROR]: Commandline can not be executed!!!"
		print "ABORTING!!!"
		sys.exit(2)
	return True


def parse_mothur_logfile(logfile, keyword, output_container, mode=None):
	if mode == 'file':
		f = open(logfile, 'rU')
		data = f.read().split('\n')
	else:
		data = logfile
	for line in data.split('\n'):
		if keyword in line:
			output_container.append(line)
	if len(output_container) < 1:
		return False
	return True


def mothur_make_file(processors, outputdir, stderr, stdout, run_pid, mothur_exec_path, input_file_directory):
	# grab path of paired fastq files and save it into container
	mothur_input_dictionary = {}
	command = 'make.file'
	mothur_input_dictionary['command'] = command
	mothur_input_dictionary['mothur_exec_path'] = mothur_exec_path
	mothur_input_dictionary['processors'] = processors
	mothur_input_dictionary['outputdir'] = outputdir
	mothur_input_dictionary['nohup_in'] = 'nohup'
	mothur_input_dictionary['nohup_out'] = '> ' + stdout + ' 2> ' + stderr + ' & echo $! > ' + run_pid
	parameter_list = []
	parameter_list.append('inputdir=' + input_file_directory)
	mothur_input_dictionary['parameters'] = parameter_list
	#here we construct the object
	make_file_object = mothur_process(mothur_input_dictionary)
	exec_dict = {}
	flag, exec_dict = make_file_object.execute_mothur_command()
	if flag is False:
		print "[FATAL-ERROR]: Commandline can not be executed!!!"
		print "ABORTING!!!"
		sys.exit(2)
	return True
# ################################# BOWTIE FUNCTIONS ########################### #


def test_bowtie(processors, outputdir, stderr, stdout, run_pid, bowtie_exec_path):
	space = ' '
	bowtie_string = 'nohup' + space + bowtie_exec_path + space + '--version' + space + '> ' + stdout + ' 2> ' + stderr + ' & echo $! > ' + run_pid
	print "EXECUTING: ", bowtie_string
	report(bowtie_string)
	exec_dict = {}
	exec_dict = execute([bowtie_string])
	if exec_dict["exitCode"] != 0:
		print "[FATAL-ERROR]: Commandline can not be executed!!!"
		print "ABORTING!!!"
		sys.exit(2)
	else:
		return True


def test_samtools(processors, outputdir, stderr, stdout, run_pid, samtools_exec_path):
	space = ' '
	samtools_string = 'nohup' + space + samtools_exec_path + space + '--version' + space + '> ' + stdout + ' 2> ' + stderr + ' & echo $! > ' + run_pid
	print "EXECUTING: ", samtools_string
	report(samtools_string)
	exec_dict = {}
	exec_dict = execute([samtools_string])
	if exec_dict["exitCode"] != 0:
		print "[FATAL-ERROR]: Commandline can not be executed!!!"
		print "ABORTING!!!"
		sys.exit(2)
	else:
		return True


def test_macs(processors, outputdir, stderr, stdout, run_pid, macs_exec_path):
	space = ' '
	macs_string = 'nohup' + space + macs_exec_path + space + '--version' + space + '> ' + stderr + ' 2> ' + stdout + ' & echo $! > ' + run_pid
	print "EXECUTING: ", macs_string
	report(macs_string)
	exec_dict = {}
	exec_dict = execute([macs_string])
	if exec_dict["exitCode"] != 0:
		print "[FATAL-ERROR]: Commandline can not be executed!!!"
		print "ABORTING!!!"
		sys.exit(2)
	else:
		return True


def bowtie_alignment(processors, outputdir, stderr, stdout, run_pid, bowtie_exec_path, input_fastq, output_sam, index_dir):
	space = ' '
	bowtie_string = 'nohup' + space + bowtie_exec_path + space
	bowtie_string += index_dir + space
	bowtie_string += '-p' + space + processors + space
	bowtie_string += '-q' + space + input_fastq + space
	bowtie_string += '-S' + space + output_sam + space
	bowtie_string += '--verbose > ' + stdout + ' 2> ' + stderr + ' & echo $! > ' + run_pid
	print "EXECUTING: ", bowtie_string
	report(bowtie_string)
	exec_dict = {}
	exec_dict = execute([bowtie_string])
	if exec_dict["exitCode"] != 0:
		print "[FATAL-ERROR]: Commandline can not be executed!!!"
		print "ABORTING!!!"
		sys.exit(2)
	else:
		return True


def sam_to_bam_converter(processors, outputdir, stderr, stdout, run_pid, samtools_exec_path, sam_file, bam_file):
	space = ' '
	sam_string = 'nohup' + space + samtools_exec_path + space
	sam_string += 'view -q30 -Sb' + space + sam_file + space + '>' + space + bam_file
	sam_string += ' 2> ' + stderr + ' & echo $! > ' + run_pid
	print "EXECUTING: ", sam_string
	report(sam_string)
	exec_dict = {}
	exec_dict = execute([sam_string])
	if exec_dict["exitCode"] != 0:
		print "[FATAL-ERROR]: Commandline can not be executed!!!"
		print "ABORTING!!!"
		sys.exit(2)
	else:
		return True
# ################################### MACS FUNCTION ############################ #


def macs_peakcalling(processors, outputdir, stderr, stdout, run_pid, macs_exec_path, sample_DT, name):
	space = ' '
	macs_string = 'nohup' + space + macs_exec_path + space
	macs_string += 'callpeak' + space
	macs_string += '-t' + space + sample_DT['test'] + space
	if 'control' in sample_DT:
		macs_string += '-c' + space + sample_DT['control'] + space
	macs_string += '-q 0.01 -f BAM -g hs -n' + space + name + space
	macs_string += '--verbose 3' + space
	macs_string += '--outdir' + space + outputdir + space
	macs_string += '> ' + stdout + ' 2> ' + stderr + ' & echo $! > ' + run_pid
	print "EXECUTING: ", macs_string
	report(macs_string)
	exec_dict = {}
	exec_dict = execute([macs_string])
	if exec_dict["exitCode"] != 0:
		print "[FATAL-ERROR]: Commandline can not be executed!!!"
		print "ABORTING!!!"
		sys.exit(2)
	else:
		return True

# ################################### SPECIFIC ################################ #


def process_inputdir(input_file_directory, files_PATH, mothur_exec_PATH, processors_COUNT, outputdir_PATH):
	file_string = ''
	for each_file in os.listdir(input_file_directory):
		if each_file.endswith(".fastq") or each_file.endswith(".fq"):
			path, absname, extension = split_file_name(each_file)
			file_string += absname + '\t' + input_file_directory + each_file + '\n'
	write_string_down(file_string, files_PATH)
	return True

	stderr = ''
	# ###################################################################################################################################### #
	flag, stderr = execute_functions(mothur_make_file, processors_COUNT, outputdir_PATH, 'multi', 'mothur', mothur_exec_PATH, input_file_directory)
	if flag is False:
		error("[" + FAILED_MARK + "]")
		print "[", FAILED_MARK, "]"
		print "Execution of mothur failed!!!"
		error("Execution of mothur failed!!!")
		print "ABORTING!!!"
		error("ABORTING!!!")
		sys.exit(2)
	else:
		#it has the file name in it
		scanned_container_list = []
		extension_list = ['.files']
		flag = scandirs(outputdir_PATH, scanned_container_list, extension_list, 'partial')
		print "Scanning.."
		if flag is False:
			print "Failed :("
			print "This extension is not available: ", extension_list
			sys.exit(2)
		else:
			print "NICE :) Found it"
			counter = 1
			for file in scanned_container_list:
				print "File#", str(counter), ":", file
				counter += 1
		file_string = ''
		f = open(scanned_container_list[0], 'rU')
		for i in f:
			i = i.rstrip()
			line = i.split('\t')
			Library_ID = line[0].split('_')[0]
			file_string += Library_ID + '\t' + line[1] + '\t' + line[2] + '\n'
		write_string_down(file_string, files_PATH)
	return True


def process_design(Excel_HD, Design_File_PATH, Input_File_PATH):
	Metadata_DF = text_to_pandas_dataframe_converter(Design_File_PATH, Skiprows_Value=None, Index_Value=None)
	Metadata_DF_LT = Metadata_DF.columns.values.tolist()
	Metadata_Sample_ID_LT = []
	Sample_ID_counter = 1
	for each_Line in Metadata_DF.iterrows():
		Metadata_Sample_ID_LT.append('DESIGN_ID_' + str(Sample_ID_counter).zfill(3))
		Sample_ID_counter += 1
	Metadata_DF = Metadata_DF.set_index([Metadata_Sample_ID_LT])
	Metadata_DF.index.name = 'DESIGN_ID'
	Metadata_DF.to_excel(Excel_HD, sheet_name='Design_Data', columns=Metadata_DF_LT, header=True, index=True, startrow=0, startcol=0)
	#Process design file and create The DICT
	Design_MATRIX = {}
	Design_MATRIX_LT = []
	for indx, row in Metadata_DF.iterrows():

		if row['control_pairs'] not in Design_MATRIX:

			Design_MATRIX[row['control_pairs']] = {}
			Design_MATRIX[row['control_pairs']][row['SampleName']] = {}
			Design_MATRIX[row['control_pairs']][row['SampleName']]['Antibody'] = row['Antibody']
			Design_MATRIX[row['control_pairs']][row['SampleName']]['design'] = row['test_control']
			Design_MATRIX_LT.append(row['control_pairs'])
		else:
			Design_MATRIX[row['control_pairs']][row['SampleName']] = {}
			Design_MATRIX[row['control_pairs']][row['SampleName']]['Antibody'] = row['Antibody']
			Design_MATRIX[row['control_pairs']][row['SampleName']]['design'] = row['test_control']
	return (True, Design_MATRIX, Design_MATRIX_LT)


def process_alignment(Files_PATH, Index_PATH, Bowtie_Exec_PATH, Samtools_Exec_PATH, processors_COUNT, outputdir_PATH):
	File_HD = open(Files_PATH, 'rU')
	for each_File in File_HD:
		File_LT = each_File.rstrip().split('\t')
		if len(File_LT) == 3:
			print "Paired end file detected"
		elif len(File_LT) == 2:
			print "Single end file detected"
			File_Name = File_LT[0]
			File_PATH = File_LT[1]
			SAM_File = outputdir_PATH + File_Name + '.sam'
			BAM_File = outputdir_PATH + File_Name + '.bam'
			flag = execute_functions(bowtie_alignment, processors_COUNT, outputdir_PATH, 'multi', 'mafft', Bowtie_Exec_PATH, File_PATH, SAM_File, Index_PATH)
			if flag is True:
				pass
			print "Convert SAM format to BAM..."
			flag = execute_functions(sam_to_bam_converter, processors_COUNT, outputdir_PATH, 'multi', 'mafft', Samtools_Exec_PATH, SAM_File, BAM_File)
			if flag is True:
				pass
	return True


def process_macs(Excel_HD, Design_MATRIX, Design_MATRIX_LT, Macs_Exec_PATH, processors_COUNT, outputdir_PATH):
	for each_Group in Design_MATRIX_LT:
		macs_sample_input = {}
		Sample_Name_LT = Design_MATRIX[each_Group].keys()
		for each_Sample in Sample_Name_LT:
			if Design_MATRIX[each_Group][each_Sample]['design'] == 'test':
				macs_sample_input['test'] = outputdir_PATH + each_Sample + '.bam'
			elif Design_MATRIX[each_Group][each_Sample]['design'] == 'control':
				macs_sample_input['control'] = outputdir_PATH + each_Sample + '.bam'
		flag = execute_functions(macs_peakcalling, processors_COUNT, outputdir_PATH, 'multi', 'mafft', Macs_Exec_PATH, macs_sample_input, 'Group_' + str(each_Group))
		if flag is True:
			pass
		Excel_File_PATH = outputdir_PATH + 'Group_' + str(each_Group) + '_peaks.xls'
		Each_Group_DF = pandas.read_table(Excel_File_PATH, low_memory=False, encoding='utf-8', comment="#", skip_blank_lines=True, error_bad_lines=False)
		Each_Group_DF.to_excel(Excel_HD, sheet_name='Group_' + str(each_Group) + '_peaks_report', columns=Each_Group_DF.columns.tolist(), header=True, index=False, startrow=0, startcol=0)
	return True
# ################################### MAIN FUNCTION ########################### #


def main(argv):
	report_string = ''
	# ++++++++++++++++++++++++++++++ PARSE INPUT ARGUMENTS
	parser = argparse.ArgumentParser()
	main_file = parser.add_argument_group('Main file parameters')
	main_file.add_argument("--design", help="Design file gives information about samples and controls", required=True)
	args = parser.parse_args()
	# ------------------------------ END OF PARSE INPUT ARGUMENTS

	# ++++++++++++++++++++++++++++++ BEURACRATICS PROCEDURES
	report_string += "######################################################################################################################################\n"
	print "######################################################################################################################################"
	report_string += "ChIps 1.0 EXECUTION HAS INITIATED" + '\n'
	print "ChIps 1.0 EXECUTION HAS INITIATED"
	report_string += "Initiation time: " + time.strftime("%Y-%m-%d %H:%M:%S") + '\n'
	print "Initiation time: ", time.strftime("%Y-%m-%d %H:%M:%S")
	report_string += "###################################################################" + '\n'
	print "###################################################################"
	report_string += "INFORMATION ABOUT THE ENVIRONMENT, EXECUTABLES AND PROVIDED DATA" + '\n'
	print "INFORMATION ABOUT THE ENVIRONMENT, EXECUTABLES AND PROVIDED DATA"
	report_string += "###################################################################" + '\n'
	print "###################################################################"
	report_string += "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++" + '\n'
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	print "COMMAND LINE:"
	report_string += "COMMAND LINE:\n"
	report_string += "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++" + '\n'
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	commandline_string = 'python ' + ' '.join(sys.argv) + '\n'
	print commandline_string
	report_string += commandline_string + '\n'
	report_string += "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++" + '\n'
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report_string += "ARGUMENTS:" + '\n'
	print "ARGUMENTS:"
	report_string += "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++" + '\n'
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	# ++++++++++++++++++++++++++++++ INPUT DIRECTORY CHECKING
	args.inputdir = DEFAULT_INPUTDIR
	# ------------------------------ END OF INPUT DIRECTORY CHECKING
	# ++++++++++++++++++++++++++++++ OUTPUT DIRECTORY CHECKING
	args.outputdir = DEFAULT_OUTPUTDIR
	global report_file
	report_file = args.outputdir + "ChIps_report.txt"
	check_it_and_remove_it(report_file, True)
	report(report_string)
	# ------------------------------ END OF OUTPUT DIRECTORY CHECKING

	# ++++++++++++++++++++++++++++++ PROCESSORS CHECKING
	args.processors = DEFAULT_PROCESSORS
	# ------------------------------ END OF PROCESSORS CHECKING

	# ++++++++++++++++++++++++++++++ PREFIX NAME CHECKING
	args.prefix = DEFAULT_PREFIX
	# ------------------------------ END OF PREFIX NAME CHECKING

	# ++++++++++++++++++++++++++++++ EXECUTIVE DIRECTORY CHECKING
	args.execdir = DEFAULT_EXECDIR
	# ------------------------------ END OF EXECUTIVE DIRECTORY CHECKING

	# ++++++++++++++++++++++++++++++ INDEX DIRECTORY CHECKING
	args.indexdir = DEFAULT_INDEXDIR + 'hg19/genome'
	# ------------------------------ END OF INDEX DIRECTORY CHECKING

	# ++++++++++++++++++++++++++++++ CHECKING EXECUTIVES
	print "\n###################################################################"
	report("\n###################################################################")
	print "VERIFYING THE SANITY/VERSION OF EXECUTABLES IN EXECUTIVE DIRECTORY[--execdir]"
	report("VERIFYING THE SANITY/VERSION OF EXECUTABLES IN EXECUTIVE DIRECTORY[--execdir]")
	print "###################################################################\n"
	report("###################################################################\n")
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	report("0: ENVIRONMENT")
	print "0: ENVIRONMENT"
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	print "Operating System version is: ", platform.platform()
	report("Operating System version is: " + platform.platform())
	python_version = sys.version.split(' (')[0]
	print "Python version is: ", python_version
	report("Python version is: " + python_version)
	if float(python_version[0:3]) < 2.7:
		error("Python version is older than 2.7")
		print "Python version is older than 2.7"
		print "ABORTING!!!"
		error("ABORTING!!!")
		sys.exit(2)
	print "Number of available CPU core: ", DEFAULT_PROCESSORS
	report("Number of available CPU core: " + DEFAULT_PROCESSORS)
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	report("1: MOTHUR")
	print "1: MOTHUR"
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	mothur_exec_PATH = args.execdir + 'mothur/mothur'
	if isFileExist(mothur_exec_PATH) is False:
		error("Your mothur file path has Access/Exist issue")
		print "Your mothur file path has Access/Exist issue"
		print "ABORTING!!!"
		error("ABORTING!!!")
		sys.exit(2)
	else:
		print "mothur execution file path is: ", mothur_exec_PATH
		report("mothur execution file path is: " + mothur_exec_PATH)
		#report("Testing mothur executables: ")
		print "Testing mothur executable: "
		report("Testing mothur executable: ")
		flag, stderr = execute_functions(test_mothur, args.processors, args.outputdir, 'multi', 'mothur', mothur_exec_PATH)
		if flag is False:
			error("[" + FAILED_MARK + "]")
			print "[", FAILED_MARK, "]"
			print "Execution of mothur failed!!!"
			error("Execution of mothur failed!!!")
			print "ABORTING!!!"
			error("ABORTING!!!")
			sys.exit(2)
		else:
			target_lines = []
			flag = parse_mothur_logfile(stderr, 'mothur v.', target_lines)
			if flag is False:
				print "This keyword is not avalaible: mothur v."
				error("This keyword is not avalaible: mothur v.")
				print "ABORTING!!!"
				error("ABORTING!!!")
				sys.exit(2)
			report("Mothur executables responding successfully!!!")
			print "Mothur executables responding successfully!!!"
			report("version of mothur executables: " + target_lines[0])
			print "version of mothur executables:", target_lines[0]
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	report("2: BOWTIE")
	print "2: BOWTIE"
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	Bowtie_Exec_PATH = args.execdir + 'bowtie/bowtie-1.2/bowtie'
	if isFileExist(Bowtie_Exec_PATH) is False:
		error("Your BOWTIE path has Access/Exist issue" + Bowtie_Exec_PATH)
		print "Your BOWTIE path has Access/Exist issue", Bowtie_Exec_PATH
		print "ABORTING!!!"
		error("ABORTING!!!")
		sys.exit(2)
	else:
		report("Bowtie execution file is: " + Bowtie_Exec_PATH)
		print "Bowtie execution file is: ", Bowtie_Exec_PATH
		report("Testing Bowtie executables: ")
		print "Testing Bowtie executables:"
		flag, stderr = execute_functions(test_bowtie, args.processors, args.outputdir, 'multi', 'mafft', Bowtie_Exec_PATH)
		if flag is False:
			print "Execution of Bowtie failed!!!"
			error("Execution of Bowtie failed!!!")
			print "ABORTING!!!"
			error("ABORTING!!!")
			sys.exit(2)
		else:
			report("Bowtie executables responding successfully!!!")
			print "Bowtie executables responding successfully!!!"
			report("version of Bowtie executables: \n" + stderr)
			print "version of Bowtie executables:\n", stderr
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	report("3: SAMTOOLS")
	print "3: SAMTOOLS"
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	Samtools_Exec_PATH = args.execdir + 'samtools/samtools-1.3.1/samtools'
	if isFileExist(Samtools_Exec_PATH) is False:
		error("Your SAMTOOLS path has Access/Exist issue" + Samtools_Exec_PATH)
		print "Your SAMTOOLS path has Access/Exist issue", Samtools_Exec_PATH
		print "ABORTING!!!"
		error("ABORTING!!!")
		sys.exit(2)
	else:
		report("SAMTOOLS execution file is: " + Samtools_Exec_PATH)
		print "SAMTOOLS execution file is: ", Samtools_Exec_PATH
		report("Testing SAMTOOLS executables: ")
		print "Testing SAMTOOLS executables:"
		flag, stderr = execute_functions(test_samtools, args.processors, args.outputdir, 'multi', 'mafft', Samtools_Exec_PATH)
		if flag is False:
			print "Execution of SAMTOOLS failed!!!"
			error("Execution of SAMTOOLS failed!!!")
			print "ABORTING!!!"
			error("ABORTING!!!")
			sys.exit(2)
		else:
			report("SAMTOOLS executables responding successfully!!!")
			print "SAMTOOLS executables responding successfully!!!"
			report("version of SAMTOOLS executables: \n" + stderr)
			print "version of SAMTOOLS executables:\n", stderr
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	report("4: MACS")
	print "4: MACS"
	print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	report("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
	Macs_Exec_PATH = args.execdir + 'macs/MACS2-2.1.1.20160309/bin/macs2'
	if isFileExist(Macs_Exec_PATH) is False:
		error("Your MACS path has Access/Exist issue" + Macs_Exec_PATH)
		print "Your MACS path has Access/Exist issue", Macs_Exec_PATH
		print "ABORTING!!!"
		error("ABORTING!!!")
		sys.exit(2)
	else:
		report("MACS execution file is: " + Macs_Exec_PATH)
		print "MACS execution file is: ", Macs_Exec_PATH
		report("Testing MACS executables: ")
		print "Testing MACS executables:"
		flag, stderr = execute_functions(test_macs, args.processors, args.outputdir, 'multi', 'mafft', Macs_Exec_PATH)
		if flag is False:
			print "Execution of MACS failed!!!"
			error("Execution of MACS failed!!!")
			print "ABORTING!!!"
			error("ABORTING!!!")
			sys.exit(2)
		else:
			report("MACS executables responding successfully!!!")
			print "MACS executables responding successfully!!!"
			report("version of MACS executables: \n" + stderr)
			print "version of MACS executables:\n", stderr
	# ------------------------------ END OF CHECKING EXECUTIVES
	# #####################################################################
	# END OF BEURACRATICS PROCEDURES
	# #####################################################################
	Excel_File_PATH = args.outputdir + 'ChIps_result.xlsx'
	Excel_HD = pandas.ExcelWriter(Excel_File_PATH, engine='xlsxwriter')

	# #####################################################################
	# INPUT DATA PREPARATION
	# #####################################################################
	
	print "INPUT DATA PREPARATION is in progress"
	report("INPUT DATA PREPARATION is in progress")
	print "Execution started at ", time.strftime("%Y-%m-%d %H:%M:%S")
	report("Execution started at " + time.strftime("%Y-%m-%d %H:%M:%S"))
	Files_PATH = args.outputdir + 'input_files_path_STEP1.txt'
	flag = process_inputdir(args.inputdir, Files_PATH, mothur_exec_PATH, args.processors, args.outputdir)
	if flag is True:
		print "INPUT DATA PREPARATION STEP: PASSED!!!"
		report("INPUT DATA PREPARATION STEP: PASSED!!!")
	else:
		error("INPUT DATA PREPARATION STEP: FAILED!!!")
		print "INPUT DATA PREPARATION STEP: FAILED!!!"
		print "ABORTING!!!"
		report("ABORTING!!!")
		sys.exit(2)
	print "Execution completed at ", time.strftime("%Y-%m-%d %H:%M:%S")
	report("Execution completed at " + time.strftime("%Y-%m-%d %H:%M:%S"))
	# ----------------------------- END OF INPUT DATA PREPARATION

	# #####################################################################
	# END OF INPUT DATA PREPARATION
	# #####################################################################

	# #####################################################################
	# DESIGN FILE PROCESSING
	# #####################################################################
	print "PROCESSING DESIGN FILE is in progress"
	report("PROCESSING DESIGN FILE is in progress")
	print "Execution started at ", time.strftime("%Y-%m-%d %H:%M:%S")
	report("Execution started at " + time.strftime("%Y-%m-%d %H:%M:%S"))
	
	flag, Design_MATRIX, Design_MATRIX_LT = process_design(Excel_HD, args.design, Files_PATH)
	if flag is True:
		print "PROCESSING DESIGN FILE STEP: PASSED!!!"
		report("PROCESSING DESIGN FILE STEP: PASSED!!!")
	else:
		error("PROCESSING DESIGN FILE STEP: FAILED!!!")
		print "PROCESSING DESIGN FILE STEP: FAILED!!!"
		print "ABORTING!!!"
		report("ABORTING!!!")
		sys.exit(2)
	print "Execution completed at ", time.strftime("%Y-%m-%d %H:%M:%S")
	report("Execution completed at " + time.strftime("%Y-%m-%d %H:%M:%S"))
	
	# #####################################################################
	# END OF DESIGN FILE PROCESSING
	# #####################################################################
	# ------------------------------ CHECKING INPUTDIR
	# ------------------------------ END OF CHECKING INPUTS

	print "# #####################################################################"
	print "# ALIGNMENT STEP"
	print "# #####################################################################"
	print "Alignment processing is in progress"
	report("Alignment processing is in progress")
	print "Execution started at ", time.strftime("%Y-%m-%d %H:%M:%S")
	report("Execution started at " + time.strftime("%Y-%m-%d %H:%M:%S"))
	
	flag = process_alignment(Files_PATH, args.indexdir, Bowtie_Exec_PATH, Samtools_Exec_PATH, args.processors, args.outputdir)
	if flag is True:
		print "bowtie_alignment STEP: PASSED!!!"
		report("bowtie_alignment STEP: PASSED!!!")
	else:
		error("bowtie_alignment STEP: FAILED!!!")
		print "bowtie_alignment STEP: FAILED!!!"
		print "ABORTING!!!"
		report("ABORTING!!!")
		sys.exit(2)
	print "Execution completed at ", time.strftime("%Y-%m-%d %H:%M:%S")
	report("Execution completed at " + time.strftime("%Y-%m-%d %H:%M:%S"))
	print "# #####################################################################"
	print "# END OF ALIGNMENT STEP"
	print "# #####################################################################"
	print "\n"
	print "# #####################################################################"
	print "# MACS STEP"
	print "# #####################################################################"
	print "MACS is in progress"
	report("MACS is in progress")
	print "Execution started at ", time.strftime("%Y-%m-%d %H:%M:%S")
	report("Execution started at " + time.strftime("%Y-%m-%d %H:%M:%S"))
	
	flag = process_macs(Excel_HD, Design_MATRIX, Design_MATRIX_LT, Macs_Exec_PATH, args.processors, args.outputdir)
	if flag is True:
		print "MACS STEP: PASSED!!!"
		report("MACS STEP: PASSED!!!")
	else:
		error("MACS STEP: FAILED!!!")
		print "MACS STEP: FAILED!!!"
		print "ABORTING!!!"
		report("ABORTING!!!")
		sys.exit(2)
	print "Execution completed at ", time.strftime("%Y-%m-%d %H:%M:%S")
	report("Execution completed at " + time.strftime("%Y-%m-%d %H:%M:%S"))
	print "# #####################################################################"
	print "# END OF MACS STEP"
	print "# #####################################################################"

	Excel_HD.save()
	# +++++++++++++++++++++++++++++ FINALIZING
	print "ChIps EXECUTION COMPLETED."
	report("ChIps EXECUTION COMPLETED.")
	report("Completion time: " + time.strftime("%Y-%m-%d %H:%M:%S"))
	print "Completion time: ", time.strftime("%Y-%m-%d %H:%M:%S")
	# ----------------------------- END OF FINALIZING
# ################################### FINITO ################################# #
if __name__ == "__main__": main(sys.argv[1:])