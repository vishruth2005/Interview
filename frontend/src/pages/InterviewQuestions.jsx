import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Send, X, ArrowRight, Save } from 'lucide-react';
import { Volume2, VolumeX } from 'lucide-react';

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const mic = new SpeechRecognition();

mic.continuous = true;
mic.interimResults = true;
mic.lang = 'en-US';

const InterviewQuestions = () => {
  const [isListening, setIsListening] = useState(false);
  const [currentInput, setCurrentInput] = useState('');
  const [questionId, setQuestionId] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(true);
  
  const [messages, setMessages] = useState([
    { type: 'system', content: 'Welcome to the interview! Click "Next Question" to begin.' }
  ]);

  const speak = (text) => {
    if (isSpeaking) {
      const speech = new SpeechSynthesisUtterance(text);
      speech.lang = "en-US";
      speech.rate = 1;
  
      // Get available voices
      const voices = speechSynthesis.getVoices();
  
      // Select a female voice
      const femaleVoice = voices.find(
        (voice) => voice.name.includes("Female") || voice.name.includes("Google US English")
      );
  
      if (femaleVoice) {
        speech.voice = femaleVoice;
      }
  
      speechSynthesis.speak(speech);
    } else {
      speechSynthesis.cancel(); // Stop speaking immediately
    }
  };
  
  
  

  useEffect(() => {
    handleListen();
  }, [isListening]);
  useEffect(() => {
    if (isSpeaking && messages.length > 0) {
      const lastMessage = messages[messages.length - 1]; 
      if (lastMessage.type === "system") {  // Only read system messages (questions)
        speechSynthesis.cancel(); // Stop any ongoing speech
        speak(lastMessage.content);
      }
    }
  }, [messages, isSpeaking]); 
  

  const handleListen = () => {
    if (isListening) {
      if (mic.state !== "started"){
        mic.start();
        console.log("mic has started")
      }
      mic.onend = () => {
        if (isListening) mic.start();
      };
    } else {
      mic.stop();
      mic.onend = () => {
        console.log('Stopped Mic');
      };
    }

    mic.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0])
        .map((result) => result.transcript)
        .join(' ');
      setCurrentInput(transcript);
    };

    mic.onerror = (event) => {
      console.log(event.error);
    };
  };

  const handleSubmit = (questionId) => {
    if (currentInput.trim()) {
      const newMessages = [...messages, { type: "user", content: currentInput }];
      setMessages(newMessages);
      setCurrentInput("");
      setIsListening(false);
  
      // Prepare request headers
      const myHeaders = new Headers();
      myHeaders.append("Content-Type", "application/json");
  
      // Prepare request body
      const raw = JSON.stringify(currentInput);
  
      // Define request options
      const requestOptions = {
        method: "POST",
        headers: myHeaders,
        body: raw,
        redirect: "follow",
      };
  
      // Call API with dynamic question ID
      fetch(`http://127.0.0.1:8000/interview/evaluate_answer/${questionId}`, requestOptions)
        .then((response) => response.json())
        .then((result) => {
          setMessages((prevMessages) => [
            ...prevMessages,
            { type: "bot", content: result.evaluation },
          ]);
          speak(result.evaluation)
          
        })
        .catch((error) => console.error("Error:", error));
    }
  };
  
  
  const handleNextQuestion = () => {
    
    fetch("http://127.0.0.1:8000/interview/next_question/", {
      method: "GET",
      redirect: "follow"
    })
      .then((response) => response.json())
      .then((result) => {
        setMessages([...messages, { type: "system", content: `Question ${result.question.id}: ${result.question.question}`}]);
        setQuestionId(result.question.id)
        
      })
      .catch((error) => console.error("Error fetching next question:", error));

  };
  

  const handleExit = () => {
    if (confirm('Are you sure you want to exit the interview?')) {
      setMessages([{ type: 'system', content: 'Interview ended. Thank you for your time!' }]);
    }
  };


  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="bg-black/40 backdrop-blur-xl rounded-3xl shadow-2xl overflow-hidden border border-white/10">
        {/* Chat Messages */}
        <div className="h-[60vh] overflow-y-auto p-6 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.type === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-2xl p-4 ${
                  message.type === 'user'
                    ? 'bg-green-600 text-white'
                    : 'bg-white/10 text-white backdrop-blur-md'
                }`}
              >
                {message.content}
              </div>
            </div>
          ))}
        </div>

        {/* Input Area */}
        <div className="border-t border-white/10 p-6 bg-black/30 backdrop-blur-xl">
          <div className="relative">
            {/* Stylized Input Box */}
            <div className="bg-black/60 backdrop-blur-xl rounded-2xl p-6 mb-6 shadow-lg border border-white/10">
              <div className="flex items-center justify-between mb-4">
                <div className="text-white/60 text-sm">Voice Input</div>
                <div className={`transition-all duration-300 ${isListening ? 'text-green-500' : 'text-white/60'}`}>
                  {isListening ? '● Recording...' : 'Ready to record'}
                </div>
              </div>
              <div className="min-h-[60px] text-white/90 text-lg">
                {currentInput || 'Start speaking...'}
              </div>
            </div>
            
            <div className="flex gap-3 justify-between">
              <div className="flex gap-3">
              <button
                  onClick={() => {
                    setIsListening((prev) => {
                      if (prev) {
                        handleSubmit(questionId); // Call handleSubmit when turning off
                      }
                      return !prev;
                    });
                  }}
                  className={`p-4 rounded-full ${
                    isListening ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
                  } text-white transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105`}
                >
                  {isListening ? <MicOff size={24} /> : <Mic size={24} />}
                </button>

                <button
                  
                  className="p-4 rounded-full bg-emerald-500 hover:bg-emerald-600 text-white transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  <Save size={24} />
                </button>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleExit}
                  className="px-6 py-3 rounded-full bg-red-500 hover:bg-red-600 text-white transition-all duration-300 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  <X size={24} /> Exit
                </button>
                <button 
                  onClick={() => {
                    speechSynthesis.cancel(); // Stop any ongoing speech immediately
                    setIsSpeaking((prev) => {
                      const newState = !prev;
                      if (newState && messages.length > 1) {
                        speak(messages[messages.length - 1].content); // Read the last question again
                      }
                      return newState;
                    });
                  }} 
                  className="p-4 rounded-full bg-blue-500 text-white"
                >
                  {isSpeaking ? <Volume2 size={24} /> : <VolumeX size={24} />}
                </button>

                <button
                  onClick={handleNextQuestion}
                  className="px-6 py-3 rounded-full bg-green-600 hover:bg-green-700 text-white transition-all duration-300 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  Next <ArrowRight size={24} />
                </button>
                
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewQuestions;