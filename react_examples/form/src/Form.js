import { useState } from 'react';

export default function Form() {

// States for registration
const [name, setName] = useState('');
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
const [mobile, setMobile] = useState('');

// States for checking the errors
const [submitted, setSubmitted] = useState(false);
const [error, setError] = useState(false);
const [mobileError, setMobileError] = useState(false);

// Handling the name change
const handleName = (e) => { setName(e.target.value); setSubmitted(false);
};
// Handling the email change
const handleEmail = (e) => { setEmail(e.target.value); setSubmitted(false);
};
// Handling the password change
const handlePassword = (e) => { setPassword(e.target.value); setSubmitted(false);
};
// Handling the mobile change
const handleMobile = (e) => { setMobile(e.target.value); setSubmitted(false);
};

// Handling the form submission
const handleSubmit = (e) => {
	e.preventDefault();
	setSubmitted(false);
	setError(false);
	setMobileError(false);
	
	if (name === '' || email === '' || password === '' || mobile === '') {
		setError(true);
		return
	} 
	else if (mobile.length <10){
		setMobileError(true);
		setError(false);
		return
	}
	else {
		setSubmitted(true);
		setError(false);
		setMobileError(false);
	}
};

// Showing success message
const successMessage = () => {
	return (
	<div
		className="success" style={{ display: submitted ? '' : 'none', }}>
		<h1>User {name}  email {email} successfully registered!!</h1>
	</div>
	);
};

// Showing error message if error is true
const errorMessage = () => {
	return (
	<div
		className="error" style={{display: error ? '' : 'none',}}>
		<h1>Please enter all the fields</h1>
	</div>
	);
};

// Showing error message if error is true
const mobileErrorMessage = () => {
	return (
	<div
		className="error" style={{display: mobileError ? '' : 'none',}}>
		<h1>Mobile Number is 10 digit number</h1>
	</div>
	);
};

return (
	<div className="form">
	<div>
		<h1>User Registration</h1>
	</div>

	{/* Calling to the methods */}
	<div className="messages">
		{errorMessage()}
		{successMessage()}
		{mobileErrorMessage()}
	</div>

	<form>
		{/* Labels and inputs for form data */}
		<label className="label">Name</label>
		<input onChange={handleName} className="input" value={name} type="text" />

		<label className="label">Email Address</label>
		<input onChange={handleEmail} className="input" value={email} type="email" />

		<label className="label">Mobile Number </label>
		<input onChange={handleMobile} className="input" value={mobile} type="mobile" />

		<label className="label">Password</label>
		<input onChange={handlePassword} className="input" value={password} type="password" />

		<button onClick={handleSubmit} className="btn" type="submit">
		Submit
		</button>
	</form>
	</div>
);
}
