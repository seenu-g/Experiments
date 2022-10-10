// Run npm i -D react-router-dom
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Layout from "./pages/Layout";
import Home from "./pages/Home";
import Blogs from "./pages/Blogs";
import Contact from "./pages/Contact";

import EducationList from './pages/EducationList'
import EducationForm from './pages/EducationForm'

import { ADD_EXPENSE, DELETE_EXPENSE } from './actions/types';

const myElement = (
  <ul>
    <li>Apples</li>
    <li>Bananas</li>
    <li>Cherries</li>
  </ul>
);

const items = [
  { id: 1, name: "Pizza", amount: 80, spendDate: "2020-10-10", category: "Food" },
  { id: 2, name: "Grape Juice", amount: 30, spendDate: "2020-10-12", category: "Food" },
  { id: 3, name: "Cinema", amount: 210, spendDate: "2020-10-16", category: "Entertainment" },
  { id: 4, name: "Java Programming book", amount: 242, spendDate: "2020-10-15", category: "Academic" },
  { id: 5, name: "Mango Juice", amount: 35, spendDate: "2020-10-16", category: "Food" },
  { id: 6, name: "Dress", amount: 2000, spendDate: "2020-10-25", category: "Cloth" },
  { id: 7, name: "Tour", amount: 2555, spendDate: "2020-10-29", category: "Entertainment" },
  { id: 8, name: "Meals", amount: 300, spendDate: "2020-10-30", category: "Food" },
  { id: 9, name: "Mobile", amount: 3500, spendDate: "2020-11-02", category: "Gadgets" },
  { id: 10, name: "Exam Fees", amount: 1245, spendDate: "2020-11-04", category: "Academic" }
]

function expensesReducer(state = [], action) {
   switch (action.type) {
      case ADD_EXPENSE:
         return [...state, action.payload];
      case DELETE_EXPENSE:
         return state.filter(expense => expense.id !== action.payload.id);
      default:
         return state;
   }
}

/*
An application can have multiple <Routes>. <Route>s can be nested. 
The first <Route> has a path of / and renders the Layout component.
The nested <Route>s inherit and add to the parent route.
The Home component route does not have a path but has an index attribute.
 That specifies this route as the default route for the parent route, which is /.

*/
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="/list" element={ <EducationList />} />
          <Route path="/add" element={ <EducationForm />} />
          <Route path="blogs" element={<Blogs />} />
          <Route path="contact" element={<Contact />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App ; 
