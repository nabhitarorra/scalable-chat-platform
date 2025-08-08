import React, { useState, useEffect, useRef } from 'react';

function ChatRoom({ user, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const ws = useRef(null);

  useEffect(() => {
    // Fetch initial messages
    fetch('http://localhost:8000/messages/')
      .then(res => res.json())
      .then(data => setMessages(data));

    // Connect to WebSocket
    ws.current = new WebSocket(`ws://localhost:8000/ws/${user.username}`);

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prevMessages) => [...prevMessages, message]);
    };

    ws.current.onclose = () => {
      console.log('WebSocket Disconnected');
    };

    // Cleanup on component unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [user.username]);

  const sendMessage = (e) => {
    e.preventDefault();
    if (newMessage.trim() && ws.current) {
      ws.current.send(newMessage);
      setNewMessage('');
    }
  };

  return (
    <div className="chat-container">
      <h2>Chat Room</h2>
      <p>Welcome, {user.username}!</p>
      <button onClick={onLogout} style={{width: "100px", marginBottom: "10px"}}>Logout</button>
      <ul className="message-list">
        {messages.map((msg, index) => (
          <li key={index}>
            <strong>{msg.username}:</strong> {msg.text}
          </li>
        ))}
      </ul>
      <form onSubmit={sendMessage} className="chat-input">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type a message..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}

export default ChatRoom;