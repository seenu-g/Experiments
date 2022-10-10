import React from 'react';
import { Link } from 'react-router-dom'

class EducationForm extends React.Component {
   constructor(props) {
      super(props);
   }
   render() {
      return (
         <div>
            <h1>Add Education item</h1>
            <p><Link to="/list">Click here</Link> to view new education list</p>
            <div>
               Education form
            </div>
         </div>
      )
   }
}
export default EducationForm;