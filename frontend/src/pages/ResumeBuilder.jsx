import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PDFDownloadLink, Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';

const styles = StyleSheet.create({
  page: {
    padding: 30,
    fontFamily: 'Helvetica',
  },
  name: {
    fontSize: 24,
    textAlign: 'center',
    marginBottom: 15,
    fontWeight: 'bold',
    color: '#2D3748',
  },
  section: {
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 14,
    marginBottom: 8,
    color: '#4A5568',
    fontWeight: 'bold',
    borderBottom: '1 solid #E2E8F0',
    paddingBottom: 4,
  },
  education: {
    marginBottom: 8,
  },
  degreeTitle: {
    fontSize: 10,
    fontWeight: 'bold',
    marginBottom: 1,
  },
  institution: {
    fontSize: 9,
    marginBottom: 1,
  },
  dates: {
    fontSize: 8,
    color: '#718096',
  },
  experience: {
    marginBottom: 10,
  },
  companyName: {
    fontSize: 10,
    fontWeight: 'bold',
    marginBottom: 3,
  },
  contribution: {
    fontSize: 8,
    marginBottom: 2,
    paddingLeft: 8,
  },
  project: {
    marginBottom: 10,
  },
  projectName: {
    fontSize: 10,
    fontWeight: 'bold',
    marginBottom: 3,
  },
  projectContent: {
    fontSize: 8,
    marginBottom: 2,
    paddingLeft: 8,
  },
  skillSection: {
    marginBottom: 8,
  },
  skillType: {
    fontSize: 9,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  skillList: {
    fontSize: 8,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
  },
  skill: {
    backgroundColor: '#EDF2F7',
    padding: '2 4',
    borderRadius: 2,
    marginRight: 4,
    marginBottom: 2,
  },
});

const ResumePDF = ({ formData }) => {
  const data = {
    full_name: "Vishruth Srivatsa",
    targetRole: formData.role,
    githubRepos: formData.repos,
    linkedinUrl: formData.linkedin,
    education: [
      {
        degree_title: "Bachelor of Technology",
        start_date: "1st August 2023",
        end_date: "30th April 2027",
        institution_name: "National Institute of Technology Karnataka"
      },
      {
        degree_title: "Higher Secondary Education",
        start_date: "1st June 2021",
        end_date: "30th April 2023",
        institution_name: "BASE PU College"
      }
    ],
    experience: [
      {
        company_details: "Web Enthusiasts' Club NITK",
        contribution_1: "Participated in Unfold'24 hackathon and built a project called JusticeChain",
        contribution_2: "Participated in EthIndia'2k24 and won the pool prize of CDP for building a project called AIgentX",
        contribution_3: "Participated in Hackverse 5.0 and won the Fintech track for building a project called Viresco"
      },
      {
        company_details: "IEEE",
        contribution_1: "Organised an event called BlackBox",
        contribution_2: "Held a talk on machine learning for first years.",
      },
      {
        company_details: "Genesis NITK",
        contribution_1: "Participated in several college level dance competitions",
        contribution_2: "Won second place in college level group dance competition as part of Genesis crew",
      }
    ],
    projects: [
      {
        name: "Lexify",
        content1: "Developed an AI-powered virtual courtroom simulation platform utilizing React, Three.js, and Redux Toolkit for the frontend, and FastAPI, PostgreSQL, and Redis for the backend.",
        content2: "Implemented AI agents powered by Gemini, LlamaIndex, and PhiData for argument simulation, impartial judging, and legal consulting, featuring document verification and legal citation checking.",
        content3: "Deployed the platform with Docker, incorporating natural language processing for dynamic interactions and a live scoring system to track user performance."
      },
      {
        name: "AIgentX",
        content1: "Designed and built a decentralized marketplace for AI agents leveraging React, FastAPI, and GraphQL, with smart contract deployment on the Base Chain and Coinbase CDP.",
        content2: "Implemented natural language processing for creating and customizing autonomous AI agents with individual wallets, incorporating real-time indexing with The Graph and decentralized storage.",
        content3: "Developed features for dual monetization and a community-driven rating system, addressing challenges in dynamic agent generation and blockchain integration using Walrus."
      }
    ],
    skills: [
      {
        type: "AI/ML Skills",
        skills: ["Natural Language Processing (NLP)", "Machine Learning (ML)", "AI Agents", "Gemini", "LlamaIndex"]
      },
      {
        type: "Data Analysis Skills",
        skills: ["Data Modeling", "Data Storage", "Data Querying", "Data Visualization", "Real-time Data Analysis"]
      },
      {
        type: "Programming and Tools",
        skills: ["Python", "FastAPI", "React", "Docker", "PostgreSQL"]
      }
    ]
  };

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <Text style={styles.name}>{data.full_name}</Text>
        <Text style={[styles.institution, { textAlign: 'center', marginBottom: 10 }]}>
          {data.targetRole} | {data.linkedinUrl}
        </Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Education</Text>
          {data.education.map((edu, index) => (
            <View key={index} style={styles.education}>
              <Text style={styles.degreeTitle}>{edu.degree_title}</Text>
              <Text style={styles.institution}>{edu.institution_name}</Text>
              <Text style={styles.dates}>{edu.start_date} - {edu.end_date}</Text>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Experience</Text>
          {data.experience.map((exp, index) => (
            <View key={index} style={styles.experience}>
              <Text style={styles.companyName}>{exp.company_details}</Text>
              <Text style={styles.contribution}>• {exp.contribution_1}</Text>
              {exp.contribution_2 && <Text style={styles.contribution}>• {exp.contribution_2}</Text>}
              {exp.contribution_3 && <Text style={styles.contribution}>• {exp.contribution_3}</Text>}
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Projects</Text>
          {data.projects.map((project, index) => (
            <View key={index} style={styles.project}>
              <Text style={styles.projectName}>{project.name}</Text>
              <Text style={styles.projectContent}>• {project.content1}</Text>
              <Text style={styles.projectContent}>• {project.content2}</Text>
              <Text style={styles.projectContent}>• {project.content3}</Text>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>GitHub Repositories</Text>
          {data.githubRepos.map((repo, index) => (
            <Text key={index} style={styles.contribution}>• {repo}</Text>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Skills</Text>
          {data.skills.map((skillGroup, index) => (
            <View key={index} style={styles.skillSection}>
              <Text style={styles.skillType}>{skillGroup.type}</Text>
              <View style={styles.skillList}>
                {skillGroup.skills.map((skill, skillIndex) => (
                  <Text key={skillIndex} style={styles.skill}>{skill}</Text>
                ))}
              </View>
            </View>
          ))}
        </View>
      </Page>
    </Document>
  );
};

function ResumeBuilder() {
  const [formData, setFormData] = useState({
    role: '',
    repos: [''],
    linkedin: '',
  });

  const addRepo = () => {
    setFormData(prev => ({
      ...prev,
      repos: [...prev.repos, ''],
    }));
  };

  const updateRepo = (index, value) => {
    const newRepos = [...formData.repos];
    newRepos[index] = value;
    setFormData(prev => ({
      ...prev,
      repos: newRepos,
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-6">Resume Builder</h1>
          
          <div className="space-y-6">
            <div>
              <label className="block text-gray-700 mb-2">Target Role</label>
              <input
                type="text"
                className="input-field"
                value={formData.role}
                onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                placeholder="e.g. Senior Software Engineer"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2">GitHub Repositories</label>
              {formData.repos.map((repo, index) => (
                <input
                  key={index}
                  type="text"
                  className="input-field mb-2"
                  value={repo}
                  onChange={(e) => updateRepo(index, e.target.value)}
                  placeholder="Repository URL"
                  required
                />
              ))}
              <button
                onClick={addRepo}
                className="text-primary hover:text-opacity-80"
                type="button"
              >
                + Add Another Repository
              </button>
            </div>

            <div>
              <label className="block text-gray-700 mb-2">LinkedIn Profile</label>
              <input
                type="text"
                className="input-field"
                value={formData.linkedin}
                onChange={(e) => setFormData(prev => ({ ...prev, linkedin: e.target.value }))}
                placeholder="LinkedIn Profile URL"
                required
              />
            </div>

            <div className="flex justify-between">
              <Link to="/" className="btn-primary bg-gray-500">
                Back
              </Link>
              <PDFDownloadLink
                document={<ResumePDF formData={formData} />}
                fileName="resume.pdf"
                className="btn-primary"
              >
                {({ loading }) => loading ? 'Generating PDF...' : 'Generate PDF'}
              </PDFDownloadLink>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ResumeBuilder;