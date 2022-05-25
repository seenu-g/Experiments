import ReactDOM from 'react-dom'
//import React from 'react';
import React, { useState } from 'react';

/*
function Button() {
  const [counter, setCounter] = useState(1);
	return <button onClick={() => setCounter(counter+1)}>{counter}</button>;

	// return <button>Stateless Button!</button>;
}

ReactDOM.render(
  <Button />, 
  document.getElementById('root'),
); 

export default Button;

*/

function Button(props) {
	return (
  	<button onClick={props.onClickFunction}>
      "Click To Increment!"
    </button>
  );
}

/* data can now flow from the parent to the child. parent is App and child is Presentation */
/* make use of props object to send date from parent to child */
function Presentation(props) {
	return (
  	<li>{props.message}</li>
  );
}

/* To make the counter state accessible to both components, we need to create a parent component. */
function App() {
	const [counter1, addCounter] = useState(0);
  const incrementCounter = () => addCounter(counter1+1);
 
  const [counter2, reduceCounter] = useState(100);
  const decrementCounter = () => reduceCounter(counter2-1);

	return (
    <div>
      <Button onClickFunction={incrementCounter}  />
      <Presentation message={counter1}/>

     <Button onClickFunction={decrementCounter}  />
     <Presentation message={counter2}/>
   </div> 
  );
}

ReactDOM.render(
  <App />, 
  document.getElementById('root'),
);

export default App;