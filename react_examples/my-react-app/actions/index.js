For example, action for adding an item in the store contains ADD_ITEM as type and an object with item’s details as payload.
 Action creator creates an action with proper action type and data necessary for  action and returns  action.
*/

import { v4 as uuidv4 } from 'uuid';
import { ADD_EXPENSE, DELETE_EXPENSE } from './types';

/*
function expects expense object and 
return action type of ADD_EXPENSE along with a payload of expense information.
*/
export const addExpense = ({ name, amount, spendDate, category }) => ({
    type: ADD_EXPENSE,
    payload: {
       id: uuidv4(),
       name,
       amount,
       spendDate,
       category
    }
 });
 /* function expects id of the expense item to be deleted and 
 return action type of ‘DELETE_EXPENSE’ along with a payload of expense id. */
 export const deleteExpense = id => ({
    type: DELETE_EXPENSE,
    payload: {
       id
    }
 });
