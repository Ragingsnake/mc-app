import React, { useState, useEffect } from 'react';
import { playClick } from '../audio';
import PublishPopup from './PublishPopup';
import { templateStory } from '../data';

export default function Play({ setView }) {
    const [displayedText, setDisplayedText] = useState("");
    const [showPopup, setShowPopup] = useState(false);
    const [generatedStory, setGeneratedStory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [displayedProtagonists, setDisplayedProtagonists] = useState([]);
    const [displayedParagraphs, setDisplayedParagraphs] = useState([]);
    const [displayedChats, setDisplayedChats] = useState([]);
    const [currentTime, setCurrentTime] = useState("");
    const [activeTypingText, setActiveTypingText] = useState("");
    const [activeTypingChat, setActiveTypingChat] = useState(null);

    useEffect(() => {
        if (window.APP_ENV === 'dev') {
            setGeneratedStory({ content: templateStory, author: "System" });
            setLoading(false);
            return;
        }
        
        let interval;
        const fetchWithRetry = (url, options = {}, retries = 3) => {
            return fetch(url, options).then(res => {
                if (res.status >= 500 && retries > 0) {
                    console.log(`Server returned ${res.status}. Retrying... (${retries} retries left)`);
                    return new Promise(resolve => setTimeout(resolve, 1000))
                        .then(() => fetchWithRetry(url, options, retries - 1));
                }
                return res;
            });
        };

        fetchWithRetry('/api/generate')
            .then(res => res.json())
            .then(data => {
                if (data.correlation_id) {
                    interval = setInterval(() => {
                        fetchWithRetry(`/api/status/${data.correlation_id}`)
                             .then(r => r.json())
                             .then(statusData => {
                                 if (statusData.status === 'done') {
                                     clearInterval(interval);
                                     let storyText = statusData.story.story;
                                     if (!storyText && statusData.story.story_parts) {
                                         storyText = statusData.story.story_parts.join("\n\n");
                                     }
                                     setGeneratedStory({ 
                                         content: storyText || "", 
                                         story_events: statusData.story.story_events,
                                         chat_log: statusData.story.chat_log
                                     });
                                     setLoading(false);
                                 } else if (statusData.status === 'error') {
                                     clearInterval(interval);
                                     setGeneratedStory({ content: "Error: " + statusData.error });
                                     setLoading(false);
                                 }
                             })
                             .catch(err => console.error("Poll error:", err));
                    }, 200);
                } else {
                    setGeneratedStory({ content: data.story || "Unknown error" });
                    setLoading(false);
                }
            })
            .catch(err => {
                console.error(err);
                setGeneratedStory({ content: "Error generating story.", author: "System" });
                setLoading(false);
            });
            
        return () => { if (interval) clearInterval(interval); };
    }, []);

    const chatContainerRef = React.useRef(null);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [displayedChats, activeTypingChat]);

    useEffect(() => {
        if (!generatedStory || !generatedStory.story_events) return;
        let eventIdx = 0;
        let charIdx = 0;
        let chatLineIdx = 0;
        let chatCharIdx = 0;
        let timeout;

        setDisplayedParagraphs([]);
        setDisplayedChats([]);
        setDisplayedProtagonists([]);
        setCurrentTime("");
        setActiveTypingText("");
        setActiveTypingChat(null);

        function runEvent() {
            if (eventIdx >= generatedStory.story_events.length) return;

            const event = generatedStory.story_events[eventIdx];
            setDisplayedProtagonists(event.protagonists);
            if (event.time) setCurrentTime(event.time);

            // Phase 1: Type the narrative text
            if (event.text && event.text.trim()) {
                charIdx = 0;
                setActiveTypingText("");
                
                function typeText() {
                    if (charIdx < event.text.length) {
                        setActiveTypingText(event.text.substring(0, charIdx + 1));
                        charIdx++;
                        timeout = setTimeout(typeText, 12);
                    } else {
                        setDisplayedParagraphs(prev => [...prev, event.text]);
                        setActiveTypingText("");
                        chatLineIdx = 0;
                        typeChatLines();
                    }
                }
                typeText();
            } else {
                chatLineIdx = 0;
                typeChatLines();
            }
        }

        function typeChatLines() {
            const event = generatedStory.story_events[eventIdx];
            if (event.chat_lines && chatLineIdx < event.chat_lines.length) {
                const chatLine = event.chat_lines[chatLineIdx];
                chatCharIdx = 0;
                
                function typeChatChar() {
                    if (chatCharIdx < chatLine.message.length) {
                        const partialMsg = chatLine.message.substring(0, chatCharIdx + 1);
                        setActiveTypingChat({ speaker: chatLine.speaker, message: partialMsg });
                        chatCharIdx++;
                        timeout = setTimeout(typeChatChar, 25);
                    } else {
                        setDisplayedChats(prev => [...prev, chatLine]);
                        setActiveTypingChat(null);
                        chatLineIdx++;
                        timeout = setTimeout(typeChatLines, 450);
                    }
                }
                typeChatChar();
            } else {
                eventIdx++;
                charIdx = 0;
                timeout = setTimeout(runEvent, 800);
            }
        }

        runEvent();
        return () => clearTimeout(timeout);
    }, [generatedStory]);

    const formatItemName = (itemId) => {
        if (!itemId) return "";
        return itemId
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    const renderProtagonists = () => {
        if (!displayedProtagonists) return null;
        return displayedProtagonists.map((pro, idx) => (
            <div key={idx} style={{ padding: '10px', backgroundColor: '#333', marginBottom: '10px', borderRadius: '5px' }}>
                <h3 style={{ margin: '0 0 10px 0', color: pro.status === 'dead' ? '#ff5555' : pro.status === 'left' ? '#aaaaaa' : '#55ff55' }}>
                    {pro.name} {pro.status !== 'alive' && `(${pro.status})`}
                </h3>
                <p style={{ margin: '5px 0', fontSize: '14px' }}>HP: {pro.health}/20</p>
                <p style={{ margin: '5px 0', fontSize: '14px' }}>Loc: {pro.location}</p>
                <p style={{ margin: '5px 0', fontSize: '14px' }}>Inv: {pro.inventory.map(formatItemName).join(', ')}</p>
            </div>
        ));
    };

    return (
        <React.Fragment>
            <div style={{ display: 'flex', width: '95%', maxWidth: '1200px', height: '68vh', gap: '20px', marginBottom: '20px', alignItems: 'stretch' }}>
                {/* Left Panel: Players */}
                <div style={{ flex: '1.2', minWidth: '220px', overflowY: 'auto', padding: '15px', backgroundColor: 'rgba(0,0,0,0.6)', border: '2px solid #333', borderRadius: '4px', display: 'flex', flexDirection: 'column' }}>
                    <h3 style={{ color: 'white', marginTop: 0, textAlign: 'center', borderBottom: '1px solid #555', paddingBottom: '10px' }}>Players</h3>
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                        {renderProtagonists()}
                    </div>
                </div>

                {/* Right Panel: Split between Storyboard (top) and Chat (bottom) */}
                <div style={{ flex: '3.5', display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    {/* Storyboard Panel */}
                    <div className="story-box" style={{ flex: '2', margin: 0, width: '100%', maxWidth: 'none', boxSizing: 'border-box', overflowY: 'auto', textAlign: 'left', padding: '20px', minHeight: '180px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {loading ? "Generating story..." : (
                            <React.Fragment>
                                {currentTime && (
                                    <div style={{ color: '#ffaa00', fontWeight: 'bold', borderBottom: '1px solid #444', paddingBottom: '5px', fontSize: '13px', fontFamily: 'monospace' }}>
                                        {currentTime.toUpperCase()}
                                    </div>
                                )}
                                <div style={{ lineHeight: '1.6', fontSize: '15px', flex: 1, overflowY: 'auto' }}>
                                    {displayedParagraphs.map((para, idx) => (
                                        <p key={idx} style={{ margin: '0 0 12px 0' }}>{para}</p>
                                    ))}
                                    {activeTypingText && <p style={{ margin: '0 0 12px 0' }}>{activeTypingText}</p>}
                                </div>
                            </React.Fragment>
                        )}
                    </div>

                    {/* Chat Logs Panel */}
                    <div style={{ flex: '1.2', margin: 0, width: '100%', maxWidth: 'none', boxSizing: 'border-box', overflowY: 'auto', padding: '15px', backgroundColor: 'rgba(0,0,0,0.85)', border: '2px solid #555', borderRadius: '4px', textAlign: 'left', minHeight: '120px', fontFamily: 'monospace', display: 'flex', flexDirection: 'column' }}>
                        <div style={{ color: '#55ff55', borderBottom: '1px solid #333', paddingBottom: '5px', marginBottom: '8px', fontSize: '11px', letterSpacing: '1px', fontWeight: 'bold' }}>SYSTEM & PLAYER CHAT</div>
                        <div ref={chatContainerRef} style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px' }}>
                            {displayedChats.map((chat, idx) => {
                                if (chat.speaker === 'System') {
                                    return <div key={idx} style={{ color: '#ffff55' }}>[System] {chat.message}</div>;
                                } else {
                                    return (
                                        <div key={idx} style={{ color: '#ffffff' }}>
                                            <span style={{ color: '#55ffff' }}>&lt;{chat.speaker}&gt;</span> {chat.message}
                                        </div>
                                    );
                                }
                            })}
                            {activeTypingChat && (
                                <div style={{ color: '#ffffff', opacity: 0.8 }}>
                                    {activeTypingChat.speaker === 'System' ? (
                                        <span style={{ color: '#ffff55' }}>[System] {activeTypingChat.message}</span>
                                    ) : (
                                        <React.Fragment>
                                            <span style={{ color: '#55ffff' }}>&lt;{activeTypingChat.speaker}&gt;</span> {activeTypingChat.message}
                                        </React.Fragment>
                                    )}
                                    <span style={{ marginLeft: '2px', animation: 'blink 0.8s infinite' }}>_</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
            <div className="button-group" style={{flexDirection: 'row', justifyContent: 'center', width: '90%', maxWidth: '1200px', gap: '15px'}}>
                <button className="mc-button" style={{flex: 1, margin: 0}} onClick={() => { playClick(); setView('home'); }}>Back</button>
                <button className="mc-button" style={{flex: 1, margin: 0}} onClick={() => { playClick(); setView('play_restart'); }}>Restart</button>
                <button className="mc-button" style={{flex: 1, margin: 0}} disabled={loading} onClick={() => { playClick(); setShowPopup(true); }}>Publish</button>
            </div>
            {showPopup && <PublishPopup setView={setView} story={generatedStory} onClose={() => { playClick(); setShowPopup(false); }} />}
        </React.Fragment>
    );
}
