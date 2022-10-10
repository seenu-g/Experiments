import React from 'react';
import { Link } from 'react-router-dom'

class EducationList extends React.Component {
   constructor(props) {
      super(props);
   }
   render() {
      return (
         <div>
            <h1>Education</h1>
            <p><Link to="/add">Click here</Link> to add new expenses</p>
            <div>
               Expense list
            </div>
         </div>
      )
   }
}
export default EducationList;