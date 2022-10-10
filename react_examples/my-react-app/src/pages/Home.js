import React from 'react';
import {Link } from "react-router-dom";

const Home = () => {
  return (
  <> 
    <h1>Home</h1>
    <div>
            <nav>
               <ul>
                  <li>
                     <Link to="/list">List Education</Link>
                  </li>
                  <li>
                     <Link to="/add">Add Education</Link>
                  </li>
               </ul>
            </nav>
    </div>
  </>
  )
};

export default Home;
