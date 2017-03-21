# ################################### INFO ##################################### #
# CHIPS
# Author: Amir Shams
# Date: Mar-16-2017
# Email: amir.shams84@gmail.com
# Aim: A simple Snakemake workflow to process ChIp-seq data.
# ################################### IMPORT ##################################### #
from os.path import join
from os.path import basename
import os
# ################################### FUNCTIONS ####################### #
def get_absname(the_file):
	#
	name = basename(the_file).split('.')
	return '.'.join(name[:-1])


def get_extension(the_file):
	return basename(the_file).split('.')[-1]


def process_samples(Sample_LT):
	Sample_DT = {}
	for each_sample in Sample_LT:
		Sample_Name = get_absname(each_sample)
		Sample_DT[Sample_Name] = {}
		Sample_DT[Sample_Name]['FULL_PATH'] = each_sample
		Sample_DT[Sample_Name]['EXTENSION'] = get_extension(each_sample)

	return Sample_DT
# ################################### WORKING DIRECTORY ####################### #
configfile: "config.yaml"
WDIR = config["WDIR"]
if WDIR is None:
	sys.exit("Working Directory are needed")
elif WDIR[-1] != '/':
	WDIR += '/'

print("The current working directory is " + WDIR)
# ################################### PROCESSING SAMPLES ####################### #
fastq_files = config["fastq_files"]

if fastq_files is None:
    sys.exit("Fastq files are needed")


Sample_DT = process_samples(fastq_files)


rule all:
	input: 
		expand(WDIR + '{sample}_model.pdf', sample=Sample_DT.keys())


rule bowtie:
	input:  lambda wildcards: Sample_DT[wildcards.sample]['FULL_PATH'] 
	output: WDIR + '{sample}.sam'
	threads: 8
	log: WDIR + 'bowtie.log'
	shell:
		"""
		module load bowtie/1.1.1
		bt_threads=$(({threads} - 2))
		bowtie {config[idx_bt1]} --threads=$bt_threads -q {input} -S {output} 2> {log}
		"""

rule samtools:
	input:  WDIR + '{sample}.sam'
	output: WDIR + '{sample}.bam'
	shell:
		"""
		module load samtools/1.3.1
		samtools view -q30 -Sb {input} > {output}
		"""

rule macs:
	input:	WDIR + '{sample}.bam'
	output: WDIR + "{sample}_model.r",
			WDIR + "{sample}_peaks.narrowPeak"
	log: "macs.log"
	shell:
		"""
		module load macs/2.1.0.20150420
		macs2 callpeak -t {input} -f BAM -g hs --outdir ./ -n {wildcards.sample} -q 0.01 --verbose 3 &> {log}
		"""
rule modelling:
	input:	WDIR + '{sample}_model.r'
	output: WDIR + "{sample}_model.pdf"
	shell:
		"""
		module load R
		Rscript {input}
		"""